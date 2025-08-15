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
        self.base_url = app.config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.default_model = app.config.get('OLLAMA_MODEL', 'llama3.1:8b')
        self.embed_model = app.config.get('EMBED_MODEL', 'nomic-embed-text')
    
    def generate_response(self, prompt: str, model: Optional[str] = None, 
                         temperature: float = 0.7, top_p: float = 0.9) -> str:
        """Generate response from Ollama LLM."""
        start_time = time.time()
        model = model or self.default_model
        
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
                f"{self.base_url}/api/generate",
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
    
    def generate_embedding(self, text: str, model: Optional[str] = None) -> Optional[List[float]]:
        """Generate embedding vector for text."""
        model = model or self.embed_model
        
        try:
            payload = {
                "model": model,
                "prompt": text
            }
            
            response = requests.post(
                f"{self.base_url}/api/embeddings",
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
    
    def list_models(self) -> List[Dict[str, str]]:
        """List available models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            
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
    
    def health_check(self) -> bool:
        """Check if Ollama service is healthy."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
