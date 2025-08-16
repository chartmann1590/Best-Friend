from typing import List, Dict, Optional, Tuple
from flask import current_app
from app.models import Memory, Message
from app import db
from app.logging_config import log_memory_operation, log_performance, log_error
import logging
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self, app):
        self.app = app
        self.max_memories = 1000  # Maximum memories per user
        self.memory_retention_days = 365  # Keep memories for 1 year
    
    def create_memory(self, user_id: int, content: str, memory_type: str = 'conversation',
                      importance: float = 1.0, metadata: Optional[Dict] = None) -> Optional[Memory]:
        """Create a new memory with embedding."""
        start_time = time.time()
        
        try:
            # Generate embedding for the content
            embedding = self._generate_embedding(content, user_id)
            if not embedding:
                log_error(
                    Exception("Embedding generation failed"),
                    f"Failed to generate embedding for memory: {content[:100]}..."
                )
                return None
            
            # Create memory
            memory = Memory(
                user_id=user_id,
                content=content,
                embedding=embedding,
                memory_type=memory_type,
                importance=importance,
                metadata=metadata or {}
            )
            
            db.session.add(memory)
            db.session.commit()
            
            # Log memory creation
            log_memory_operation(
                'create',
                user_id,
                f"Type: {memory_type}, Importance: {importance}, Content length: {len(content)}"
            )
            
            # Log performance
            duration = time.time() - start_time
            log_performance('memory_creation', duration, f"User: {user_id}, Type: {memory_type}")
            
            return memory
            
        except Exception as e:
            log_error(e, f"Error creating memory for user {user_id}")
            db.session.rollback()
            return None
    
    def search_memories(self, user_id: int, query: str, limit: int = 10, 
                       threshold: float = 0.7) -> List[Tuple[Memory, float]]:
        """Search memories using vector similarity."""
        start_time = time.time()
        
        try:
            # Generate embedding for query
            query_embedding = self._generate_embedding(query, user_id)
            if not query_embedding:
                return []
            
            # Vector similarity search using pgvector
            memories = db.session.query(Memory).filter(
                Memory.user_id == user_id
            ).order_by(
                Memory.embedding.cosine_distance(query_embedding)
            ).limit(limit).all()
            
            # Calculate similarity scores and filter by threshold
            results = []
            for memory in memories:
                similarity = 1 - memory.embedding.cosine_distance(query_embedding)
                if similarity >= threshold:
                    results.append((memory, similarity))
            
            # Sort by similarity score (highest first)
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Log memory search
            log_memory_operation(
                'search',
                user_id,
                f"Query: {query[:50]}..., Results: {len(results)}, Threshold: {threshold}"
            )
            
            # Log performance
            duration = time.time() - start_time
            log_performance('memory_search', duration, f"User: {user_id}, Results: {len(results)}")
            
            return results
            
        except Exception as e:
            log_error(e, f"Error searching memories for user {user_id}")
            return []
    
    def get_recent_memories(self, user_id: int, days: int = 7, limit: int = 20) -> List[Memory]:
        """Get recent memories from the last N days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            memories = Memory.query.filter(
                Memory.user_id == user_id,
                Memory.created_at >= cutoff_date
            ).order_by(Memory.created_at.desc()).limit(limit).all()
            
            return memories
            
        except Exception as e:
            logger.error(f"Error getting recent memories: {str(e)}")
            return []
    
    def get_important_memories(self, user_id: int, limit: int = 20) -> List[Memory]:
        """Get memories with high importance scores."""
        try:
            memories = Memory.query.filter(
                Memory.user_id == user_id,
                Memory.importance >= 0.8
            ).order_by(Memory.importance.desc()).limit(limit).all()
            
            return memories
            
        except Exception as e:
            logger.error(f"Error getting important memories: {str(e)}")
            return []
    
    def update_memory_importance(self, memory_id: int, new_importance: float) -> bool:
        """Update memory importance score."""
        try:
            memory = Memory.query.get(memory_id)
            if memory:
                memory.importance = max(0.0, min(1.0, new_importance))
                memory.last_accessed = datetime.utcnow()
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating memory importance: {str(e)}")
            db.session.rollback()
            return False
    
    def cleanup_old_memories(self, user_id: int) -> int:
        """Remove old memories beyond retention period."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.memory_retention_days)
            
            # Delete old, low-importance memories
            deleted_count = Memory.query.filter(
                Memory.user_id == user_id,
                Memory.created_at < cutoff_date,
                Memory.importance < 0.5
            ).delete()
            
            db.session.commit()
            logger.info(f"Cleaned up {deleted_count} old memories for user {user_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old memories: {str(e)}")
            db.session.rollback()
            return 0
    
    def create_conversation_memory(self, user_id: int, messages: List[Message]) -> Optional[Memory]:
        """Create a memory from a conversation."""
        if not messages:
            return None
        
        # Combine recent messages into a summary
        recent_content = []
        for msg in messages[-5:]:  # Last 5 messages
            role = "You" if msg.role == "user" else "AI"
            recent_content.append(f"{role}: {msg.content}")
        
        conversation_text = "\n".join(recent_content)
        
        # Create memory with conversation type
        return self.create_memory(
            user_id=user_id,
            content=conversation_text,
            memory_type='conversation',
            importance=0.8,
            metadata={'message_count': len(messages)}
        )
    
    def _generate_embedding(self, text: str, user_id: int) -> Optional[List[float]]:
        """Generate embedding using Ollama."""
        try:
            ollama_client = current_app.ollama_client
            return ollama_client.generate_embedding(text, user_id)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def get_memory_stats(self, user_id: int) -> Dict[str, int]:
        """Get memory statistics for a user."""
        try:
            total = Memory.query.filter_by(user_id=user_id).count()
            conversations = Memory.query.filter_by(
                user_id=user_id, 
                memory_type='conversation'
            ).count()
            facts = Memory.query.filter_by(
                user_id=user_id, 
                memory_type='fact'
            ).count()
            preferences = Memory.query.filter_by(
                user_id=user_id, 
                memory_type='preference'
            ).count()
            
            return {
                'total': total,
                'conversations': conversations,
                'facts': facts,
                'preferences': preferences
            }
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            return {'total': 0, 'conversations': 0, 'facts': 0, 'preferences': 0}
