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
            
            # 2. User profile context
            user_context = self._build_user_context(user)
            if user_context:
                prompt_parts.append(f"\n{user_context}")
            
            # 3. Recent conversation context
            conversation_context = self._build_conversation_context(user_id)
            if conversation_context:
                prompt_parts.append(f"\n{conversation_context}")
            
            # 4. Relevant memories
            memory_context = self._build_memory_context(user_id, current_message)
            if memory_context:
                prompt_parts.append(f"\n{memory_context}")
            
            # 5. Current message context
            if current_message:
                prompt_parts.append(f"\nCurrent user message: {current_message}")
            
            # 6. Response guidelines
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
        
        # Get user preferences
        preferences = self._get_user_preferences(user.id)
        if preferences:
            context_parts.append(f"User preferences: {preferences}")
        
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
            
            context_parts = ["Recent conversation:"]
            for msg in recent_messages:
                role = "User" if msg.role == "user" else "You"
                context_parts.append(f"{role}: {msg.content}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error building conversation context: {str(e)}")
            return ""
    
    def _build_memory_context(self, user_id: int, current_message: str) -> str:
        """Build context from relevant memories."""
        try:
            if not current_message:
                return ""
            
            # Search for relevant memories
            memory_service = current_app.memory_service
            relevant_memories = memory_service.search_memories(
                user_id=user_id,
                query=current_message,
                limit=self.max_memory_snippets,
                threshold=0.6
            )
            
            if not relevant_memories:
                return ""
            
            context_parts = ["Relevant memories:"]
            for memory, similarity in relevant_memories:
                context_parts.append(f"- {memory.content} (relevance: {similarity:.2f})")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error building memory context: {str(e)}")
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
    
    def _get_response_guidelines(self) -> str:
        """Get guidelines for AI responses."""
        return """
Response Guidelines:
- Keep responses conversational and engaging
- Use the user's name when appropriate
- Reference relevant memories when helpful
- Ask follow-up questions to continue the conversation
- Be concise but thorough
- Show empathy and understanding
- Maintain a consistent, friendly tone"""
    
    def build_chat_prompt(self, user_id: int, user_message: str) -> str:
        """Build a prompt specifically for chat responses."""
        system_prompt = self.build_system_prompt(user_id, user_message)
        
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
