from typing import List, Optional
from flask import current_app
from app.models import Message, Memory
from app import db
import logging
from datetime import datetime, timedelta
from rq import get_current_job

logger = logging.getLogger(__name__)

def summarize_conversation(user_id: int, conversation_id: str) -> Optional[Memory]:
    """Summarize a conversation and create a memory."""
    try:
        # Get messages for the conversation
        messages = Message.query.filter_by(
            user_id=user_id,
            conversation_id=conversation_id
        ).order_by(Message.timestamp.asc()).all()
        
        if not messages:
            logger.warning(f"No messages found for conversation {conversation_id}")
            return None
        
        # Build conversation text
        conversation_text = ""
        for msg in messages:
            role = "User" if msg.role == "user" else "AI"
            conversation_text += f"{role}: {msg.content}\n"
        
        # Create summary using AI
        prompt_service = current_app.prompt_service
        summary_prompt = prompt_service.build_summary_prompt(user_id, messages)
        
        ollama_client = current_app.ollama_client
        summary = ollama_client.generate_response(summary_prompt, user_id)
        
        if summary:
            # Create memory from summary
            memory_service = current_app.memory_service
            memory = memory_service.create_memory(
                user_id=user_id,
                content=summary,
                memory_type='conversation_summary',
                importance=0.7,
                metadata={
                    'conversation_id': conversation_id,
                    'message_count': len(messages),
                    'summary_type': 'auto_generated'
                }
            )
            
            logger.info(f"Created conversation summary memory for user {user_id}")
            return memory
        
        return None
        
    except Exception as e:
        logger.error(f"Error summarizing conversation: {str(e)}")
        return None

def cleanup_old_memories(user_id: int) -> int:
    """Clean up old, low-importance memories."""
    try:
        memory_service = current_app.memory_service
        deleted_count = memory_service.cleanup_old_memories(user_id)
        
        logger.info(f"Cleaned up {deleted_count} old memories for user {user_id}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up old memories: {str(e)}")
        return 0

def compact_memories(user_id: int) -> int:
    """Compact similar memories to reduce redundancy."""
    try:
        memory_service = current_app.memory_service
        
        # Get recent memories
        recent_memories = memory_service.get_recent_memories(user_id, days=30, limit=100)
        
        if len(recent_memories) < 10:
            return 0  # Not enough memories to compact
        
        compacted_count = 0
        
        # Group memories by type
        memories_by_type = {}
        for memory in recent_memories:
            if memory.memory_type not in memories_by_type:
                memories_by_type[memory.memory_type] = []
            memories_by_type[memory.memory_type].append(memory)
        
        # Compact memories of the same type
        for memory_type, memories in memories_by_type.items():
            if len(memories) < 3:
                continue
            
            # Find similar memories and merge them
            for i, memory1 in enumerate(memories):
                if memory1.id is None:  # Already processed
                    continue
                
                for j, memory2 in enumerate(memories[i+1:], i+1):
                    if memory2.id is None:  # Already processed
                        continue
                    
                    # Check similarity
                    similarity = memory_service._calculate_similarity(memory1, memory2)
                    if similarity > 0.8:  # High similarity threshold
                        # Merge memories
                        merged_content = f"{memory1.content}\n\n{memory2.content}"
                        
                        # Update first memory
                        memory1.content = merged_content
                        memory1.importance = max(memory1.importance, memory2.importance)
                        memory1.last_accessed = datetime.utcnow()
                        
                        # Mark second memory for deletion
                        memory2.id = None
                        compacted_count += 1
        
        # Remove marked memories
        for memory in recent_memories:
            if memory.id is None:
                db.session.delete(memory)
        
        db.session.commit()
        
        logger.info(f"Compacted {compacted_count} memories for user {user_id}")
        return compacted_count
        
    except Exception as e:
        logger.error(f"Error compacting memories: {str(e)}")
        db.session.rollback()
        return 0

def update_memory_importance(user_id: int) -> int:
    """Update memory importance scores based on usage patterns."""
    try:
        updated_count = 0
        
        # Get memories that haven't been updated recently
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        memories = Memory.query.filter(
            Memory.user_id == user_id,
            Memory.last_accessed < cutoff_date
        ).all()
        
        for memory in memories:
            # Calculate new importance based on age and type
            age_days = (datetime.utcnow() - memory.created_at).days
            
            # Base importance decreases with age
            base_importance = max(0.1, 1.0 - (age_days / 365))
            
            # Adjust based on memory type
            type_multiplier = {
                'conversation': 0.8,
                'preference': 1.0,
                'fact': 0.9,
                'conversation_summary': 0.7
            }.get(memory.memory_type, 0.8)
            
            new_importance = base_importance * type_multiplier
            
            # Update if significantly different
            if abs(memory.importance - new_importance) > 0.1:
                memory.importance = new_importance
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            logger.info(f"Updated importance for {updated_count} memories for user {user_id}")
        
        return updated_count
        
    except Exception as e:
        logger.error(f"Error updating memory importance: {str(e)}")
        db.session.rollback()
        return 0

def scheduled_maintenance():
    """Run scheduled maintenance tasks."""
    try:
        job = get_current_job()
        logger.info(f"Starting scheduled maintenance job: {job.id}")
        
        # Get all users
        from app.models import User
        users = User.query.filter_by(is_active=True).all()
        
        total_compacted = 0
        total_cleaned = 0
        total_updated = 0
        
        for user in users:
            try:
                # Clean up old memories
                cleaned = cleanup_old_memories(user.id)
                total_cleaned += cleaned
                
                # Compact memories
                compacted = compact_memories(user.id)
                total_compacted += compacted
                
                # Update importance scores
                updated = update_memory_importance(user.id)
                total_updated += updated
                
            except Exception as e:
                logger.error(f"Error processing user {user.id}: {str(e)}")
                continue
        
        logger.info(f"Maintenance completed: {total_cleaned} cleaned, {total_compacted} compacted, {total_updated} updated")
        
        return {
            'cleaned': total_cleaned,
            'compacted': total_compacted,
            'updated': total_updated
        }
        
    except Exception as e:
        logger.error(f"Error in scheduled maintenance: {str(e)}")
        return None
