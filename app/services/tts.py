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
        # Default fallback values (will be overridden by user settings)
        self.default_base_url = app.config.get('TTS_URL', 'http://localhost:5500')
        self.default_voice = app.config.get('TTS_VOICE', 'en_US-amy-low')
    
    def _get_user_settings(self, user_id):
        """Get TTS settings for a specific user."""
        from app.models import Setting
        
        try:
            tts_url_setting = Setting.query.filter_by(user_id=user_id, key='tts_url').first()
            tts_voice_setting = Setting.query.filter_by(user_id=user_id, key='tts_voice').first()
            
            base_url = tts_url_setting.get_value() if tts_url_setting else self.default_base_url
            voice = tts_voice_setting.get_value() if tts_voice_setting else self.default_voice
            
            return base_url, voice
        except Exception as e:
            logger.error(f"Error getting user TTS settings: {str(e)}")
            return self.default_base_url, self.default_voice
    
    def synthesize_speech(self, text: str, user_id: int, voice: Optional[str] = None, 
                         speed: float = 1.0, pitch: float = 1.0) -> Optional[bytes]:
        """Synthesize text to speech audio."""
        # Get user's TTS settings
        base_url, user_voice = self._get_user_settings(user_id)
        voice = voice or user_voice
        
        try:
            # OpenTTS synthesis endpoint - uses GET with query parameters
            url = f"{base_url}/api/tts"
            
            params = {
                'voice': voice,
                'text': text
            }
            
            # OpenTTS doesn't support speed/pitch in the basic API
            # These would need to be handled by the TTS system itself
            
            response = requests.get(
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
    
    def stream_speech(self, text: str, user_id: int, voice: Optional[str] = None,
                     speed: float = 1.0, pitch: float = 1.0) -> Optional[BinaryIO]:
        """Stream speech synthesis for real-time playback."""
        # Get user's TTS settings
        base_url, user_voice = self._get_user_settings(user_id)
        voice = voice or user_voice
        
        try:
            # OpenTTS streaming endpoint - uses GET with query parameters
            url = f"{base_url}/api/tts"
            
            params = {
                'voice': voice,
                'text': text
            }
            
            # OpenTTS doesn't support speed/pitch in the basic API
            # These would need to be handled by the TTS system itself
            
            response = requests.get(
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
    
    def get_available_voices(self, user_id: int) -> list:
        """Get list of available voices from OpenTTS API."""
        try:
            base_url, _ = self._get_user_settings(user_id)
            logger.info(f"Fetching voices from OpenTTS at: {base_url}")
            
            response = requests.get(f"{base_url}/api/voices", timeout=10)
            
            if response.status_code == 200:
                voices_data = response.json()
                voices = []
                
                # OpenTTS returns an object with voice keys
                # Format: {"espeak:en": {...}, "espeak:de": {...}, ...}
                if isinstance(voices_data, dict):
                    for voice_key, voice_info in voices_data.items():
                        # voice_key format: "tts:voice" (e.g., "espeak:en", "flite:en-us")
                        if isinstance(voice_info, dict):
                            voice = self._parse_opentts_voice(voice_key, voice_info)
                            if voice:
                                voices.append(voice)
                
                # Log the response for debugging
                logger.info(f"OpenTTS response format: {type(voices_data)}, found {len(voices)} voices")
                logger.info(f"Raw OpenTTS response: {voices_data}")
                if voices:
                    logger.info(f"Sample voice: {voices[0]}")
                else:
                    logger.warning("No voices found in OpenTTS response")
                
                return voices
            else:
                logger.error(f"OpenTTS voices API error: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenTTS voices API request failed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting OpenTTS voices: {str(e)}")
            return []
    
    def _parse_opentts_voice(self, voice_key: str, voice_info: dict) -> dict:
        """Parse OpenTTS voice data from API response."""
        try:
            # voice_key format: "tts:voice" (e.g., "espeak:en", "flite:en-us")
            # voice_info contains the voice details
            
            # Extract TTS system and voice name from key
            if ':' in voice_key:
                tts_system, voice_name = voice_key.split(':', 1)
            else:
                tts_system = 'unknown'
                voice_name = voice_key
            
            # Get voice details from voice_info
            language = voice_info.get('language', '')
            locale = voice_info.get('locale', '')
            gender = voice_info.get('gender', '')
            
            # Build display name
            display_name = f"{tts_system}:{voice_name}"
            if locale:
                display_name += f" ({locale})"
            if gender:
                display_name += f" [{gender}]"
            
            # Build description
            description_parts = []
            if tts_system:
                description_parts.append(f"TTS: {tts_system}")
            if language:
                description_parts.append(f"Language: {language}")
            if locale:
                description_parts.append(f"Locale: {locale}")
            if gender:
                description_parts.append(f"Gender: {gender}")
            
            description = " | ".join(description_parts) if description_parts else display_name
            
            return {
                'id': voice_key,  # Use the full voice key as ID (e.g., "espeak:en")
                'name': display_name,  # Human-readable display name
                'language': language or 'Unknown',
                'gender': gender or 'Unknown',
                'description': description,
                'tts_system': tts_system,
                'voice_name': voice_name,
                'locale': locale or ''
            }
            
        except Exception as e:
            logger.error(f"Error parsing OpenTTS voice {voice_key}: {str(e)}")
            return None
    
    def _parse_voice_data(self, voice: dict) -> dict:
        """Parse voice data from generic TTS API response (fallback)."""
        # Handle different field names that OpenTTS might use
        voice_id = voice.get('id') or voice.get('name') or voice.get('voice_id') or ''
        voice_name = voice.get('name') or voice.get('display_name') or voice_id or 'Unknown'
        language = voice.get('language') or voice.get('lang') or voice.get('locale') or 'Unknown'
        gender = voice.get('gender') or voice.get('sex') or 'Unknown'
        description = voice.get('description') or voice.get('desc') or voice.get('comment') or ''
        
        # Clean up the data
        if isinstance(voice_id, str):
            voice_id = voice_id.strip()
        if isinstance(voice_name, str):
            voice_name = voice_name.strip()
        if isinstance(language, str):
            language = language.strip()
        if isinstance(gender, str):
            gender = gender.strip()
        if isinstance(description, str):
            description = description.strip()
        
        return {
            'id': voice_id,
            'name': voice_name,
            'language': language,
            'gender': gender,
            'description': description
        }
    
    def get_voice_info(self, voice_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific voice."""
        try:
            base_url, _ = self._get_user_settings(user_id)
            response = requests.get(f"{base_url}/api/voices/{voice_id}", timeout=10)
            
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
    
    def test_voice(self, voice_id: str, user_id: int, test_text: str = "Hello, this is a test.") -> bool:
        """Test if a voice is working with a short text."""
        try:
            audio_data = self.synthesize_speech(test_text, user_id, voice_id)
            return audio_data is not None and len(audio_data) > 0
        except Exception as e:
            logger.error(f"Voice test failed for {voice_id}: {str(e)}")
            return False
    
    def preview_voice(self, voice_id: str, user_id: int, preview_text: str = "Hello, this is a voice preview.") -> Optional[bytes]:
        """Generate a voice preview for testing."""
        try:
            audio_data = self.synthesize_speech(preview_text, user_id, voice_id)
            return audio_data
        except Exception as e:
            logger.error(f"Voice preview failed for {voice_id}: {str(e)}")
            return None
    
    def get_supported_languages(self, user_id: int) -> list:
        """Get list of supported languages."""
        voices = self.get_available_voices(user_id)
        languages = set()
        
        for voice in voices:
            if voice.get('language'):
                languages.add(voice['language'])
        
        return sorted(list(languages))
    
    def find_voice_by_language(self, language: str, user_id: int, gender: Optional[str] = None) -> Optional[str]:
        """Find a voice ID for a specific language and optional gender."""
        voices = self.get_available_voices(user_id)
        
        for voice in voices:
            if voice.get('language') == language:
                if gender is None or voice.get('gender') == gender:
                    return voice['id']
        
        # Fallback: find any voice for the language
        for voice in voices:
            if voice.get('language') == language:
                return voice['id']
        
        return None
    
    def health_check(self, user_id: int) -> bool:
        """Check if TTS service is healthy."""
        try:
            base_url, _ = self._get_user_settings(user_id)
            response = requests.get(f"{base_url}/api/voices", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_service_info(self, user_id: int) -> Dict[str, Any]:
        """Get TTS service information."""
        try:
            base_url, _ = self._get_user_settings(user_id)
            response = requests.get(f"{base_url}/api/info", timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}
