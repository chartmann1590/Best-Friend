import requests
import json
from typing import List, Dict, Optional
from flask import current_app
from app.logging_config import log_ai_interaction, log_performance, log_error
import logging
import time

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, app):
        self.app = app
        # Default fallback values (will be overridden by user settings)
        self.default_base_url = app.config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.default_model = app.config.get('OLLAMA_MODEL', 'llama3.1:8b')
        self.embed_model = app.config.get('EMBED_MODEL', 'nomic-embed-text')
    
    def _get_user_settings(self, user_id):
        """Get Ollama settings for a specific user."""
        from app.models import Setting
        
        try:
            ollama_url_setting = Setting.query.filter_by(user_id=user_id, key='ollama_url').first()
            ollama_model_setting = Setting.query.filter_by(user_id=user_id, key='ollama_model').first()
            
            base_url = ollama_url_setting.get_value() if ollama_url_setting else self.default_base_url
            model = ollama_model_setting.get_value() if ollama_model_setting else self.default_model
            
            return base_url, model
        except Exception as e:
            logger.error(f"Error getting user Ollama settings: {str(e)}")
            return self.default_base_url, self.default_model
    
    def generate_response(self, prompt: str, user_id: int, model: Optional[str] = None, 
                         temperature: float = 0.7, top_p: float = 0.9) -> str:
        """Generate response from Ollama LLM."""
        start_time = time.time()
        
        # Get user's Ollama settings
        base_url, user_model = self._get_user_settings(user_id)
        model = model or user_model
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p
                }
            }
            
            response = requests.post(
                f"{base_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return "I'm sorry, I'm having trouble generating a response right now."
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {str(e)}")
            return "I'm sorry, I'm unable to connect to my AI model right now."
        except Exception as e:
            logger.error(f"Unexpected error in Ollama client: {str(e)}")
            return "I encountered an unexpected error while processing your request."
    
    def generate_embedding(self, text: str, user_id: int, model: Optional[str] = None) -> Optional[List[float]]:
        """Generate embedding vector for text."""
        # Get user's Ollama settings for base URL
        base_url, _ = self._get_user_settings(user_id)
        model = model or self.embed_model
        
        try:
            payload = {
                "model": model,
                "prompt": text
            }
            
            response = requests.post(
                f"{base_url}/api/embeddings",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('embedding', [])
            else:
                logger.error(f"Ollama embedding API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama embedding API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Ollama embedding: {str(e)}")
            return None
    
    def list_models(self, user_id: int) -> List[Dict[str, str]]:
        """List available models."""
        try:
            base_url, _ = self._get_user_settings(user_id)
            response = requests.get(f"{base_url}/api/tags", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('models', [])
            else:
                logger.error(f"Ollama list models error: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama list models request failed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing models: {str(e)}")
            return []
    
    def health_check(self, user_id: int) -> bool:
        """Check if Ollama service is healthy."""
        try:
            base_url, _ = self._get_user_settings(user_id)
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
