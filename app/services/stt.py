import os
import tempfile
import logging
from typing import Optional, Dict, Any
from faster_whisper import WhisperModel
from flask import current_app
import wave
import numpy as np

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self, app):
        self.app = app
        self.model = None
        self.language = app.config.get('STT_LANGUAGE', 'en')
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            # Use smaller model for faster processing
            model_size = "base"  # Options: tiny, base, small, medium, large
            self.model = WhisperModel(
                model_size,
                device="cpu",  # Use GPU if available: "cuda"
                compute_type="int8"  # Use "float16" for better accuracy
            )
            logger.info(f"Loaded Whisper model: {model_size}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            self.model = None
    
    def transcribe_audio(self, audio_file, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe audio file to text."""
        if not self.model:
            return {
                'success': False,
                'error': 'Whisper model not loaded',
                'text': '',
                'confidence': 0.0
            }
        
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                audio_file.save(temp_file.name)
                temp_path = temp_file.name
            
            try:
                # Transcribe audio
                segments, info = self.model.transcribe(
                    temp_path,
                    language=language or self.language,
                    beam_size=5,
                    best_of=5,
                    temperature=0.0,
                    compression_ratio_threshold=2.4,
                    log_prob_threshold=-1.0,
                    no_speech_threshold=0.6,
                    condition_on_previous_text=False,
                    initial_prompt=None
                )
                
                # Combine segments
                transcribed_text = ""
                total_confidence = 0.0
                segment_count = 0
                
                for segment in segments:
                    transcribed_text += segment.text + " "
                    if hasattr(segment, 'avg_logprob'):
                        total_confidence += segment.avg_logprob
                    segment_count += 1
                
                # Calculate average confidence
                avg_confidence = (total_confidence / segment_count) if segment_count > 0 else 0.0
                # Convert log probability to confidence score (0-1)
                confidence_score = max(0.0, min(1.0, (avg_confidence + 1.0) / 2.0))
                
                # Clean up temporary file
                os.unlink(temp_path)
                
                return {
                    'success': True,
                    'text': transcribed_text.strip(),
                    'confidence': confidence_score,
                    'language': info.language,
                    'language_probability': info.language_probability,
                    'segments': segment_count
                }
                
            except Exception as e:
                # Clean up temporary file on error
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise e
                
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'confidence': 0.0
            }
    
    def transcribe_audio_file(self, file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe audio from file path."""
        if not self.model:
            return {
                'success': False,
                'error': 'Whisper model not loaded',
                'text': '',
                'confidence': 0.0
            }
        
        try:
            # Transcribe audio
            segments, info = self.model.transcribe(
                file_path,
                language=language or self.language,
                beam_size=5,
                best_of=5,
                temperature=0.0
            )
            
            # Combine segments
            transcribed_text = ""
            total_confidence = 0.0
            segment_count = 0
            
            for segment in segments:
                transcribed_text += segment.text + " "
                if hasattr(segment, 'avg_logprob'):
                    total_confidence += segment.avg_logprob
                segment_count += 1
            
            # Calculate average confidence
            avg_confidence = (total_confidence / segment_count) if segment_count > 0 else 0.0
            confidence_score = max(0.0, min(1.0, (avg_confidence + 1.0) / 2.0))
            
            return {
                'success': True,
                'text': transcribed_text.strip(),
                'confidence': confidence_score,
                'language': info.language,
                'language_probability': info.language_probability,
                'segments': segment_count
            }
            
        except Exception as e:
            logger.error(f"Error transcribing audio file: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'confidence': 0.0
            }
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages."""
        return [
            'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh',
            'ar', 'hi', 'nl', 'pl', 'sv', 'da', 'no', 'fi', 'tr', 'he'
        ]
    
    def is_audio_supported(self, filename: str) -> bool:
        """Check if audio file format is supported."""
        supported_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.webm']
        return any(filename.lower().endswith(ext) for ext in supported_extensions)
    
    def health_check(self) -> bool:
        """Check if STT service is healthy."""
        return self.model is not None
