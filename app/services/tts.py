import requests
import logging
from typing import Optional, Dict, Any, BinaryIO
from flask import current_app
import tempfile
import os

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, app):
        self.app = app
        self.base_url = app.config.get('TTS_URL', 'http://localhost:5500')
        self.default_voice = app.config.get('TTS_VOICE', 'en_US-amy-low')
    
    def synthesize_speech(self, text: str, voice: Optional[str] = None, 
                         speed: float = 1.0, pitch: float = 1.0) -> Optional[bytes]:
        """Synthesize text to speech audio."""
        voice = voice or self.default_voice
        
        try:
            # OpenTTS synthesis endpoint
            url = f"{self.base_url}/api/tts"
            
            params = {
                'voice': voice,
                'text': text,
                'speed': speed,
                'pitch': pitch
            }
            
            response = requests.post(
                url,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"TTS API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in TTS: {str(e)}")
            return None
    
    def stream_speech(self, text: str, voice: Optional[str] = None,
                     speed: float = 1.0, pitch: float = 1.0) -> Optional[BinaryIO]:
        """Stream speech synthesis for real-time playback."""
        voice = voice or self.default_voice
        
        try:
            # OpenTTS streaming endpoint
            url = f"{self.base_url}/api/tts"
            
            params = {
                'voice': voice,
                'text': text,
                'speed': speed,
                'pitch': pitch
            }
            
            response = requests.post(
                url,
                params=params,
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                # Create temporary file for streaming
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                temp_file.close()
                
                # Return file object for streaming
                return open(temp_file.name, 'rb')
            else:
                logger.error(f"TTS streaming API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS streaming API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in TTS streaming: {str(e)}")
            return None
    
    def get_available_voices(self) -> list:
        """Get list of available voices."""
        try:
            response = requests.get(f"{self.base_url}/api/voices", timeout=10)
            
            if response.status_code == 200:
                voices_data = response.json()
                voices = []
                
                for voice in voices_data:
                    voices.append({
                        'id': voice.get('id', ''),
                        'name': voice.get('name', ''),
                        'language': voice.get('language', ''),
                        'gender': voice.get('gender', ''),
                        'description': voice.get('description', '')
                    })
                
                return voices
            else:
                logger.error(f"TTS voices API error: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS voices API request failed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting voices: {str(e)}")
            return []
    
    def get_voice_info(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific voice."""
        try:
            response = requests.get(f"{self.base_url}/api/voices/{voice_id}", timeout=10)
            
            if response.status_code == 200:
                voice_data = response.json()
                return {
                    'id': voice_data.get('id', ''),
                    'name': voice_data.get('name', ''),
                    'language': voice_data.get('language', ''),
                    'gender': voice_data.get('gender', ''),
                    'description': voice_data.get('description', ''),
                    'sample_rate': voice_data.get('sample_rate', 22050),
                    'quality': voice_data.get('quality', 'medium')
                }
            else:
                logger.error(f"TTS voice info API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS voice info API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting voice info: {str(e)}")
            return None
    
    def test_voice(self, voice_id: str, test_text: str = "Hello, this is a test.") -> bool:
        """Test if a voice is working with a short text."""
        try:
            audio_data = self.synthesize_speech(test_text, voice_id)
            return audio_data is not None and len(audio_data) > 0
        except Exception as e:
            logger.error(f"Voice test failed for {voice_id}: {str(e)}")
            return False
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages."""
        voices = self.get_available_voices()
        languages = set()
        
        for voice in voices:
            if voice.get('language'):
                languages.add(voice['language'])
        
        return sorted(list(languages))
    
    def find_voice_by_language(self, language: str, gender: Optional[str] = None) -> Optional[str]:
        """Find a voice ID for a specific language and optional gender."""
        voices = self.get_available_voices()
        
        for voice in voices:
            if voice.get('language') == language:
                if gender is None or voice.get('gender') == gender:
                    return voice['id']
        
        # Fallback: find any voice for the language
        for voice in voices:
            if voice.get('language') == language:
                return voice['id']
        
        return None
    
    def health_check(self) -> bool:
        """Check if TTS service is healthy."""
        try:
            response = requests.get(f"{self.base_url}/api/voices", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get TTS service information."""
        try:
            response = requests.get(f"{self.base_url}/api/info", timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}
