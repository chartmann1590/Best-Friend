from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import Setting
from app import db
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest
import requests
import json

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
def index():
    """Settings page."""
    settings = {}
    for setting in current_user.settings:
        settings[setting.key] = setting.get_value()
    
    return render_template('settings.html', settings=settings)

@settings_bp.route('/', methods=['POST'])
@login_required
def update_settings():
    """Update user settings."""
    # Validate CSRF token
    try:
        validate_csrf(request.form.get('csrf_token'))
    except BadRequest:
        flash('CSRF token validation failed. Please try again.', 'error')
        return redirect(url_for('settings.index'))
    
    settings_data = request.form.to_dict()
    # Remove csrf_token from settings data
    settings_data.pop('csrf_token', None)
    
    for key, value in settings_data.items():
        setting = Setting.query.filter_by(user_id=current_user.id, key=key).first()
        if not setting:
            setting = Setting(user_id=current_user.id, key=key)
        
        # Encrypt sensitive settings
        encrypt = key in ['ollama_url', 'tts_url']
        setting.set_value(value, encrypt=encrypt)
        db.session.add(setting)
    
    db.session.commit()
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('settings.index'))

@settings_bp.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    """Get user settings as JSON."""
    settings = {}
    for setting in current_user.settings:
        settings[setting.key] = setting.get_value()
    
    return jsonify(settings)

@settings_bp.route('/api/test-ollama', methods=['POST'])
@login_required
def test_ollama_connection():
    """Test Ollama server connection and fetch available models."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except BadRequest:
        return jsonify({'error': 'CSRF token validation failed'}), 400
    
    ollama_url = request.form.get('ollama_url', '').strip()
    if not ollama_url:
        return jsonify({'error': 'Ollama URL is required'}), 400
    
    try:
        # Test connection by listing models
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        response.raise_for_status()
        
        models_data = response.json()
        models = []
        
        if 'models' in models_data:
            for model in models_data['models']:
                models.append({
                    'name': model.get('name', ''),
                    'size': model.get('size', 0),
                    'modified_at': model.get('modified_at', ''),
                    'digest': model.get('digest', '')
                })
        
        return jsonify({
            'success': True,
            'message': f'Successfully connected to Ollama server at {ollama_url}',
            'models': models,
            'total_models': len(models)
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Failed to connect to Ollama server: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500

@settings_bp.route('/api/test-tts', methods=['POST'])
@login_required
def test_tts_connection():
    """Test TTS server connection and fetch available voices."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except BadRequest:
        return jsonify({'error': 'CSRF token validation failed'}), 400
    
    tts_url = request.form.get('tts_url', '').strip()
    if not tts_url:
        return jsonify({'error': 'TTS URL is required'}), 400
    
    try:
        # Test connection by fetching voices (OpenTTS API)
        response = requests.get(f"{tts_url}/api/voices", timeout=10)
        response.raise_for_status()
        
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
        
        # Log for debugging
        print(f"OpenTTS response format: {type(voices_data)}, found {len(voices)} voices")
        print(f"Raw OpenTTS response: {voices_data}")
        if voices:
            print(f"Sample voice: {voices[0]}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully connected to TTS server at {tts_url}',
            'voices': voices,
            'total_voices': len(voices)
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Failed to connect to TTS server: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500

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
            print(f"Error parsing OpenTTS voice {voice_key}: {str(e)}")
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

@settings_bp.route('/api/preview-voice', methods=['POST'])
@login_required
def preview_voice():
    """Preview a TTS voice with sample text."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except BadRequest:
        return jsonify({'error': 'CSRF token validation failed'}), 400
    
    voice_id = request.form.get('voice_id', '').strip()
    preview_text = request.form.get('preview_text', 'Hello, this is a voice preview.').strip()
    
    if not voice_id:
        return jsonify({'error': 'Voice ID is required'}), 400
    
    try:
        # Get TTS service and generate preview
        tts_service = current_app.tts_service
        audio_data = tts_service.preview_voice(voice_id, current_user.id, preview_text)
        
        if audio_data:
            # Return audio data as base64 encoded string
            import base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            return jsonify({
                'success': True,
                'audio_data': audio_b64,
                'message': f'Voice preview generated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate voice preview'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500
