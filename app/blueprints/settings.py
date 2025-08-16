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
        
        if isinstance(voices_data, list):
            for voice in voices_data:
                voices.append({
                    'name': voice.get('name', ''),
                    'language': voice.get('language', ''),
                    'gender': voice.get('gender', ''),
                    'description': voice.get('description', '')
                })
        elif isinstance(voices_data, dict) and 'voices' in voices_data:
            for voice in voices_data['voices']:
                voices.append({
                    'name': voice.get('name', ''),
                    'language': voice.get('language', ''),
                    'gender': voice.get('gender', ''),
                    'description': voice.get('description', '')
                })
        
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
