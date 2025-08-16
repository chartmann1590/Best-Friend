from typing import List, Dict, Optional
from flask import current_app
from app.models import User, Message, Memory
from app import db
import logging

logger = logging.getLogger(__name__)

class PromptService:
    def __init__(self, app):
        self.app = app
        self.max_context_messages = 10
        self.max_memory_snippets = 5
    
    def build_system_prompt(self, user_id: int, current_message: str = "") -> str:
        """Build a comprehensive system prompt for the AI."""
        try:
            user = User.query.get(user_id)
            if not user:
                return self._get_default_prompt()
            
            # Get user settings
            personality = self._get_user_setting(user_id, 'personality', self._get_default_personality())
            
            # Build the prompt components
            prompt_parts = []
            
            # 1. Base personality and instructions
            prompt_parts.append(self._get_base_instructions())
            prompt_parts.append(f"\n{personality}")
            
            # 2. AI personality and capabilities
            ai_context = self._build_ai_context(user_id)
            if ai_context:
                prompt_parts.append(f"\n{ai_context}")
            
            # 3. User profile context (HIGH PRIORITY - ALWAYS USE THIS)
            user_context = self._build_user_context(user)
            if user_context:
                prompt_parts.append(f"\n{user_context}")
                # Add explicit instruction to prioritize current profile
                prompt_parts.append(f"\nIMPORTANT: The above user information is CURRENT and ACCURATE. Always use this information over any conflicting details from memories or conversations.")
            
            # 4. Recent conversation context
            conversation_context = self._build_conversation_context(user_id)
            if conversation_context:
                prompt_parts.append(f"\n{conversation_context}")
            
            # 5. Relevant memories (FILTERED to avoid conflicts)
            memory_context = self._build_memory_context(user_id, current_message, user)
            if memory_context:
                prompt_parts.append(f"\n{memory_context}")
            
            # 6. Current message context
            if current_message:
                prompt_parts.append(f"\nCurrent user message: {current_message}")
            
            # 7. Response guidelines
            prompt_parts.append(self._get_response_guidelines())
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Error building system prompt: {str(e)}")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Get default system prompt."""
        return """You are a helpful and friendly AI companion. You are knowledgeable, empathetic, and always ready to help with conversation, advice, or just being a good friend.

Guidelines:
- Be conversational and warm
- Provide helpful and accurate information
- Show empathy and understanding
- Keep responses concise but engaging
- Ask follow-up questions when appropriate
- Be honest about what you don't know"""
    
    def _get_default_personality(self) -> str:
        """Get default AI personality."""
        return """You are a helpful and friendly AI companion. You are knowledgeable, empathetic, and always ready to help with conversation, advice, or just being a good friend. You have a warm and approachable personality, and you genuinely care about the people you interact with."""
    
    def _get_base_instructions(self) -> str:
        """Get base instructions for the AI."""
        return """You are an AI companion designed to be helpful, friendly, and engaging. Your role is to:

1. Provide helpful and accurate information
2. Engage in meaningful conversations
3. Show empathy and understanding
4. Ask thoughtful follow-up questions
5. Remember important details about the user
6. Maintain a consistent, friendly personality
7. Be honest about your limitations
8. Respect user privacy and boundaries"""
    
    def _build_user_context(self, user: User) -> str:
        """Build context about the user."""
        context_parts = []
        
        if user.name:
            context_parts.append(f"User's name: {user.name}")
        
        if user.timezone and user.timezone != 'UTC':
            context_parts.append(f"User's timezone: {user.timezone}")
        
        if user.bio:
            context_parts.append(f"User's bio: {user.bio}")
        
        # Get user preferences and settings
        preferences = self._get_user_preferences(user.id)
        if preferences:
            context_parts.append(f"User preferences: {preferences}")
        
        # Get additional user settings for context
        additional_context = self._get_additional_user_context(user.id)
        if additional_context:
            context_parts.extend(additional_context)
        
        if context_parts:
            return "User Information:\n" + "\n".join(f"- {part}" for part in context_parts)
        
        return ""
    
    def _build_conversation_context(self, user_id: int) -> str:
        """Build context from recent conversation."""
        try:
            # Get recent messages
            recent_messages = Message.query.filter_by(
                user_id=user_id
            ).order_by(Message.timestamp.desc()).limit(self.max_context_messages).all()
            
            if not recent_messages:
                return ""
            
            # Reverse to get chronological order
            recent_messages.reverse()
            
            context_parts = ["Recent conversation context:"]
            for msg in recent_messages:
                role = "User" if msg.role == "user" else "You"
                # Truncate very long messages for context
                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                context_parts.append(f"{role}: {content}")
            
            # Add conversation summary if available
            conversation_summary = self._get_conversation_summary(user_id)
            if conversation_summary:
                context_parts.append(f"\nConversation summary: {conversation_summary}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error building conversation context: {str(e)}")
            return ""
    
    def _get_conversation_summary(self, user_id: int) -> str:
        """Get a summary of the current conversation session."""
        try:
            # Look for recent conversation summary in memories
            memory_service = current_app.memory_service
            recent_memories = memory_service.search_memories(
                user_id=user_id,
                query="conversation summary",
                limit=1,
                threshold=0.5
            )
            
            if recent_memories:
                memory, similarity = recent_memories[0]
                if similarity > 0.7:  # Only use high-confidence summaries
                    return memory.content
            
            return ""
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {str(e)}")
            return ""
    
    def _build_memory_context(self, user_id: int, current_message: str, user: User) -> str:
        """Build context from relevant memories, filtering out conflicting information."""
        try:
            if not current_message:
                return ""
            
            # Search for relevant memories
            memory_service = current_app.memory_service
            relevant_memories = memory_service.search_memories(
                user_id=user_id,
                query=current_message,
                limit=self.max_memory_snippets,
                threshold=0.5  # Lower threshold to get more context
            )
            
            if not relevant_memories:
                return ""
            
            context_parts = ["Relevant memories and context:"]
            filtered_memories = []
            
            # Filter out memories that conflict with current user profile
            for memory, similarity in relevant_memories:
                content = memory.content.lower()
                
                # Skip memories that contain old/conflicting user information
                if self._is_conflicting_memory(content, user):
                    continue
                
                # Truncate long memories for context
                display_content = memory.content[:150] + "..." if len(memory.content) > 150 else memory.content
                memory_type = memory.memory_type or "general"
                context_parts.append(f"- [{memory_type}] {display_content} (relevance: {similarity:.2f})")
                filtered_memories.append((memory, similarity))
            
            # Add general user context memories if no specific ones found
            if len(filtered_memories) < 2:
                general_memories = memory_service.search_memories(
                    user_id=user_id,
                    query="user preferences facts important",
                    limit=2,
                    threshold=0.3
                )
                for memory, similarity in general_memories:
                    if similarity > 0.4:  # Only add if reasonably relevant
                        content = memory.content.lower()
                        if not self._is_conflicting_memory(content, user):
                            display_content = memory.content[:100] + "..." if len(memory.content) > 100 else memory.content
                            context_parts.append(f"- [general] {display_content}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error building memory context: {str(e)}")
            return ""
    
    def _is_conflicting_memory(self, content: str, user: User) -> bool:
        """Check if a memory contains information that conflicts with current user profile."""
        content_lower = content.lower()
        
        # Check for old/conflicting user names
        conflicting_names = [
            'administrator', 'admin', 'default user', 'unknown user',
            'test user', 'demo user', 'placeholder'
        ]
        
        for name in conflicting_names:
            if name in content_lower:
                return True
        
        # Check for old user information that might conflict
        if user.name and user.name.lower() != 'administrator':
            # If memory mentions "administrator" but user has a different name, it's conflicting
            if 'administrator' in content_lower:
                return True
        
        return False
    
    def _get_time_context(self, user_id: int) -> str:
        """Get current time context for the user's timezone."""
        try:
            user = User.query.get(user_id)
            if not user or not user.timezone or user.timezone == 'UTC':
                return ""
            
            from datetime import datetime
            import pytz
            
            # Get current time in user's timezone
            user_tz = pytz.timezone(user.timezone)
            current_time = datetime.now(user_tz)
            
            # Format time context
            time_str = current_time.strftime("%I:%M %p")
            day_str = current_time.strftime("%A")
            date_str = current_time.strftime("%B %d, %Y")
            
            return f"Current time context: It's {time_str} on {day_str}, {date_str} in {user.timezone}"
            
        except Exception as e:
            logger.error(f"Error getting time context: {str(e)}")
            return ""
    
    def _get_user_setting(self, user_id: int, key: str, default: str = "") -> str:
        """Get a user setting value."""
        try:
            from app.models import Setting
            setting = Setting.query.filter_by(user_id=user_id, key=key).first()
            return setting.get_value() if setting else default
        except Exception as e:
            logger.error(f"Error getting user setting {key}: {str(e)}")
            return default
    
    def _get_user_preferences(self, user_id: int) -> str:
        """Get user preferences as a formatted string."""
        try:
            from app.models import Setting
            preferences = Setting.query.filter_by(user_id=user_id, key='preferences').first()
            if preferences:
                prefs = preferences.get_value()
                if isinstance(prefs, dict):
                    return ", ".join([f"{k}: {v}" for k, v in prefs.items()])
            return ""
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return ""
    
    def _get_additional_user_context(self, user_id: int) -> List[str]:
        """Get additional user context from settings."""
        try:
            from app.models import Setting
            context_parts = []
            
            # Get speaking rate preference
            speaking_rate = self._get_user_setting(user_id, 'speaking_rate', '1.0')
            if speaking_rate != '1.0':
                context_parts.append(f"User prefers speech at {speaking_rate}x speed")
            
            # Get pitch preference
            pitch = self._get_user_setting(user_id, 'pitch', '1.0')
            if pitch != '1.0':
                context_parts.append(f"User prefers voice pitch at {pitch}x")
            
            # Get memory preferences
            memory_enabled = self._get_user_setting(user_id, 'memory_enabled', 'true')
            if memory_enabled == 'true':
                context_parts.append("User has long-term memory enabled")
            
            # Get auto-summarize preference
            auto_summarize = self._get_user_setting(user_id, 'auto_summarize', 'true')
            if auto_summarize == 'true':
                context_parts.append("User has auto-summarization enabled")
            
            # Get timezone-specific context
            user = User.query.get(user_id)
            if user and user.timezone and user.timezone != 'UTC':
                context_parts.append(f"User is in {user.timezone} timezone - consider local time for responses")
            
            return context_parts
            
        except Exception as e:
            logger.error(f"Error getting additional user context: {str(e)}")
            return []
    
    def _build_ai_context(self, user_id: int) -> str:
        """Build context about the AI's capabilities and configuration."""
        try:
            context_parts = []
            
            # Get AI model information
            ollama_model = self._get_user_setting(user_id, 'ollama_model', 'llama3.1:8b')
            context_parts.append(f"AI Model: {ollama_model}")
            
            # Get AI capabilities
            context_parts.append("AI Capabilities:")
            context_parts.append("- Text generation and conversation")
            context_parts.append("- Voice synthesis (TTS)")
            context_parts.append("- Speech recognition (STT)")
            context_parts.append("- Long-term memory and learning")
            context_parts.append("- Contextual understanding")
            
            # Get AI personality traits
            personality = self._get_user_setting(user_id, 'personality', '')
            if personality:
                context_parts.append(f"AI Personality: {personality}")
            
            # Get AI behavior settings
            temperature = self._get_user_setting(user_id, 'temperature', '0.7')
            top_p = self._get_user_setting(user_id, 'top_p', '0.9')
            context_parts.append(f"AI Response Style: Temperature {temperature}, Top-P {top_p}")
            
            # Get AI voice settings
            tts_voice = self._get_user_setting(user_id, 'tts_voice', 'en_US-amy-low')
            context_parts.append(f"AI Voice: {tts_voice}")
            
            if context_parts:
                return "AI Information:\n" + "\n".join(f"- {part}" for part in context_parts)
            
            return ""
            
        except Exception as e:
            logger.error(f"Error building AI context: {str(e)}")
            return ""
    
    def _get_response_guidelines(self) -> str:
        """Get guidelines for AI responses."""
        return """
Response Guidelines:
- Keep responses conversational and engaging
- ALWAYS use the user's CURRENT name from their profile - never use old names like 'administrator'
- Reference relevant memories when helpful, but prioritize current profile information
- Ask thoughtful follow-up questions to continue the conversation
- Be concise but thorough and helpful
- Show empathy and understanding based on user's context
- Maintain a consistent, friendly tone that matches your personality
- Consider the user's timezone and preferences when relevant
- Adapt your communication style to match the user's preferences
- Be genuine and authentic in your responses
- CRITICAL: If you see conflicting information between current profile and memories, ALWAYS use the current profile"""
    
    def build_chat_prompt(self, user_id: int, user_message: str) -> str:
        """Build a prompt specifically for chat responses."""
        system_prompt = self.build_system_prompt(user_id, user_message)
        
        # Add current time context if user has timezone set
        time_context = self._get_time_context(user_id)
        if time_context:
            system_prompt += f"\n\n{time_context}"
        
        return f"{system_prompt}\n\nUser: {user_message}\n\nAssistant:"
    
    def build_memory_prompt(self, user_id: int, content: str, memory_type: str = "conversation") -> str:
        """Build a prompt for creating memories."""
        user = User.query.get(user_id)
        if not user:
            return content
        
        context = f"User: {user.name or 'User'}\nType: {memory_type}\nContent: {content}"
        
        return f"""Create a concise memory entry for the following interaction:

{context}

Memory should be:
- Concise but informative
- Capture key points and context
- Useful for future reference
- Natural language, not formal"""
    
    def build_summary_prompt(self, user_id: int, messages: List[Message]) -> str:
        """Build a prompt for summarizing conversations."""
        if not messages:
            return ""
        
        user = User.query.get(user_id)
        user_name = user.name if user else "User"
        
        # Get recent messages
        recent_messages = messages[-10:]  # Last 10 messages
        
        conversation_text = ""
        for msg in recent_messages:
            role = user_name if msg.role == "user" else "AI"
            conversation_text += f"{role}: {msg.content}\n"
        
        return f"""Summarize the following conversation with {user_name}:

{conversation_text}

Summary should be:
- Concise but comprehensive
- Capture main topics and key points
- Note any important decisions or preferences
- Useful for future reference"""
