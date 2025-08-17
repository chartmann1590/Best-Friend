from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import Setting
from app import db
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest
import requests
import json

settings_bp = Blueprint('settings', __name__)

def _parse_opentts_voice(voice_key: str, voice_info: dict) -> dict:
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

def _parse_voice_data(voice: dict) -> dict:
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

@settings_bp.route('/')
@login_required
def index():
    """Settings page."""
    # Get user settings from Setting model
    settings = {}
    for setting in current_user.settings:
        settings[setting.key] = setting.get_value()
    
    # Add User model fields (name, bio, timezone) to settings
    # This ensures the AI can access all profile information
    if current_user.name:
        settings['name'] = current_user.name
    if current_user.bio:
        settings['bio'] = current_user.bio
    if current_user.timezone:
        settings['timezone'] = current_user.timezone
    
    return render_template('settings.html', settings=settings)

@settings_bp.route('/', methods=['POST'])
@login_required
def update_settings():
    """Update user settings and profile information."""
    # Validate CSRF token
    try:
        validate_csrf(request.form.get('csrf_token'))
    except BadRequest:
        flash('CSRF token validation failed. Please try again.', 'error')
        return redirect(url_for('settings.index'))
    
    settings_data = request.form.to_dict()
    # Remove csrf_token from settings data
    settings_data.pop('csrf_token', None)
    
    # Update User model fields (name, bio, timezone)
    if 'name' in settings_data:
        current_user.name = settings_data['name'].strip() if settings_data['name'] else None
    if 'bio' in settings_data:
        current_user.bio = settings_data['bio'].strip() if settings_data['bio'] else None
    if 'timezone' in settings_data:
        current_user.timezone = settings_data['timezone']
    
    # Update other settings in Setting model
    for key, value in settings_data.items():
        # Skip User model fields that we already handled
        if key in ['name', 'bio', 'timezone']:
            continue
            
        setting = Setting.query.filter_by(user_id=current_user.id, key=key).first()
        if not setting:
            setting = Setting(user_id=current_user.id, key=key)
        
        # Encrypt sensitive settings
        encrypt = key in ['ollama_url', 'tts_url']
        setting.set_value(value, encrypt=encrypt)
        db.session.add(setting)
    
    # Add current_user to session and commit
    db.session.add(current_user)
    db.session.commit()
    
    flash('Settings and profile updated successfully!', 'success')
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
        # Increased timeout for slow TTS servers
        current_app.logger.info(f"Testing TTS connection to: {tts_url}")
        
        response = requests.get(f"{tts_url}/api/voices", timeout=30)
        response.raise_for_status()
        
        voices_data = response.json()
        voices = []
        
        # Log raw response for debugging
        current_app.logger.info(f"TTS API response status: {response.status_code}")
        current_app.logger.info(f"TTS API response headers: {dict(response.headers)}")
        current_app.logger.info(f"TTS API response type: {type(voices_data)}")
        current_app.logger.info(f"TTS API response length: {len(str(voices_data))}")
        
        # OpenTTS returns an object with voice keys
        # Format: {"espeak:en": {...}, "espeak:de": {...}, ...}
        if isinstance(voices_data, dict):
            for voice_key, voice_info in voices_data.items():
                # voice_key format: "tts:voice" (e.g., "espeak:en", "flite:en-us")
                if isinstance(voice_info, dict):
                    voice = _parse_opentts_voice(voice_key, voice_info)
                    if voice:
                        voices.append(voice)
        
        # Log for debugging
        current_app.logger.info(f"Parsed {len(voices)} voices from TTS server")
        if voices:
            current_app.logger.info(f"Sample voice: {voices[0]}")
        
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
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500
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
        if not hasattr(current_app, 'tts_service') or not current_app.tts_service:
            return jsonify({
                'success': False,
                'error': 'TTS service not available'
            }), 500
        
        tts_service = current_app.tts_service
        
        # Debug: Log the preview request
        current_app.logger.info(f"Voice preview request: voice_id={voice_id}, user_id={current_user.id}, text_length={len(preview_text)}")
        
        audio_data = tts_service.preview_voice(voice_id, current_user.id, preview_text)
        
        if audio_data and len(audio_data) > 0:
            # Return audio data as base64 encoded string
            import base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            current_app.logger.info(f"Voice preview successful: {len(audio_data)} bytes")
            
            return jsonify({
                'success': True,
                'audio_data': audio_b64,
                'message': f'Voice preview generated successfully ({len(audio_data)} bytes)'
            })
        else:
            current_app.logger.warning(f"Voice preview failed: no audio data returned")
            return jsonify({
                'success': False,
                'error': 'Failed to generate voice preview - no audio data returned'
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Voice preview error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Voice preview failed: {str(e)}'
        }), 500

@settings_bp.route('/api/clear-memories', methods=['POST'])
@login_required
def clear_memories():
    """Clear user memories."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except BadRequest:
        return jsonify({'error': 'CSRF token validation failed'}), 400
    
    memory_type = request.form.get('memory_type', 'all')  # all, conversation, fact, preference
    
    try:
        memory_service = current_app.memory_service
        if memory_service:
            if memory_type == 'all':
                success = memory_service.clear_user_memories(current_user.id)
            elif memory_type == 'conversation':
                success = memory_service.clear_conversation_memories(current_user.id)
            elif memory_type == 'fact':
                success = memory_service.clear_fact_memories(current_user.id)
            elif memory_type == 'preference':
                success = memory_service.clear_preference_memories(current_user.id)
            else:
                return jsonify({
                    'success': False,
                    'error': f'Invalid memory type: {memory_type}'
                }), 400
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Successfully cleared {memory_type} memories'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to clear memories'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'Memory service not available'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500

@settings_bp.route('/api/memory-stats', methods=['GET'])
@login_required
def get_memory_stats():
    """Get user memory statistics."""
    try:
        # Debug: Check if memory service exists
        if not hasattr(current_app, 'memory_service') or not current_app.memory_service:
            return jsonify({
                'success': False,
                'error': 'Memory service not available'
            }), 500
        
        # Debug: Check if user has any memories directly
        from app.models import Memory
        direct_count = Memory.query.filter_by(user_id=current_user.id).count()
        
        # Get stats from memory service
        stats = current_app.memory_service.get_memory_stats(current_user.id)
        
        # Debug: Add direct count for comparison
        stats['debug_direct_count'] = direct_count
        
        return jsonify({
            'success': True,
            'stats': stats
        })
            
    except Exception as e:
        current_app.logger.error(f"Error getting memory stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500

@settings_bp.route('/api/delete', methods=['DELETE'])
@login_required
def delete_all_data():
    """Delete all user data including conversations, memories, and settings."""
    try:
        from app.models import Message, Memory
        
        # Delete all user messages
        Message.query.filter_by(user_id=current_user.id).delete()
        
        # Delete all user memories
        Memory.query.filter_by(user_id=current_user.id).delete()
        
        # Delete all user settings
        Setting.query.filter_by(user_id=current_user.id).delete()
        
        # Reset user profile to defaults
        current_user.name = None
        current_user.bio = None
        current_user.timezone = 'UTC'
        current_user.preferences = {}
        
        # Commit all changes
        db.session.commit()
        
        # Log the deletion
        current_app.logger.warning(f"User {current_user.id} ({current_user.email}) deleted all their data")
        
        return jsonify({'success': True, 'message': 'All data deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user data: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete data' }), 500

@settings_bp.route('/api/test-tts-simple', methods=['POST'])
@login_required
def test_tts_simple():
    """Simple TTS test to debug OpenTTS connection issues."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except BadRequest:
        return jsonify({'error': 'CSRF token validation failed'}), 400
    
    tts_url = request.form.get('tts_url', '').strip()
    voice = request.form.get('voice', 'espeak:en').strip()
    test_text = request.form.get('test_text', 'Hello world').strip()
    
    if not tts_url:
        return jsonify({'error': 'TTS URL is required'}), 400
    
    try:
        # Test basic TTS synthesis
        import requests
        
        # Try different OpenTTS endpoints
        endpoints = ['/api/tts', '/api/synthesize', '/api/say']
        
        for endpoint in endpoints:
            try:
                url = f"{tts_url}{endpoint}"
                params = {
                    'voice': voice,
                    'text': test_text
                }
                
                current_app.logger.info(f"Testing TTS endpoint: {url} with params: {params}")
                
                response = requests.get(url, params=params, timeout=30)
                
                current_app.logger.info(f"TTS endpoint {endpoint} response: {response.status_code}")
                
                if response.status_code == 200:
                    audio_size = len(response.content)
                    current_app.logger.info(f"TTS synthesis successful: {audio_size} bytes")
                    
                    return jsonify({
                        'success': True,
                        'message': f'TTS synthesis successful using {endpoint}',
                        'endpoint': endpoint,
                        'audio_size': audio_size,
                        'voice': voice,
                        'text': test_text
                    })
                else:
                    current_app.logger.warning(f"TTS endpoint {endpoint} failed: {response.status_code} - {response.text[:200]}")
                    
            except requests.exceptions.RequestException as e:
                current_app.logger.warning(f"TTS endpoint {endpoint} error: {str(e)}")
                continue
        
        # If we get here, all endpoints failed
        return jsonify({
            'success': False,
            'error': 'All TTS endpoints failed. Check the TTS URL and server status.'
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"TTS simple test error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'TTS test failed: {str(e)}'
        }), 500

@settings_bp.route('/api/tts-health', methods=['GET'])
@login_required
def tts_health_check():
    """Check TTS service health and connectivity."""
    try:
        if not hasattr(current_app, 'tts_service') or not current_app.tts_service:
            return jsonify({
                'success': False,
                'error': 'TTS service not available'
            }), 500
        
        # Get user's TTS settings
        from app.models import Setting
        tts_url_setting = Setting.query.filter_by(user_id=current_user.id, key='tts_url').first()
        
        if not tts_url_setting:
            return jsonify({
                'success': False,
                'error': 'TTS URL not configured'
            }), 400
        
        tts_url = tts_url_setting.get_value()
        
        # Test basic connectivity
        try:
            import requests
            response = requests.get(f"{tts_url}/api/voices", timeout=10)
            
            if response.status_code == 200:
                return jsonify({
                    'success': True,
                    'message': f'TTS server at {tts_url} is responding',
                    'response_time': f'{response.elapsed.total_seconds():.2f}s',
                    'status_code': response.status_code
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'TTS server responded with status {response.status_code}',
                    'response_text': response.text[:200]
                }), 400
                
        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': f'TTS server at {tts_url} timed out after 10 seconds'
            }), 400
        except requests.exceptions.ConnectionError:
            return jsonify({
                'success': False,
                'error': f'Cannot connect to TTS server at {tts_url}'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'TTS health check failed: {str(e)}'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"TTS health check error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500

@settings_bp.route('/api/debug-memories', methods=['GET'])
@login_required
def debug_memories():
    """Debug endpoint to see what memories exist for the user."""
    try:
        from app.models import Memory
        
        # Get all memories for the user
        memories = Memory.query.filter_by(user_id=current_user.id).all()
        
        memory_list = []
        for memory in memories:
            memory_list.append({
                'id': memory.id,
                'content': memory.content[:100] + "..." if len(memory.content) > 100 else memory.content,
                'memory_type': memory.memory_type,
                'importance': memory.importance,
                'created_at': memory.created_at.isoformat() if memory.created_at else None,
                'last_accessed': memory.last_accessed.isoformat() if memory.last_accessed else None
            })
        
        return jsonify({
            'success': True,
            'total_memories': len(memories),
            'memories': memory_list
        })
        
    except Exception as e:
        current_app.logger.error(f"Error debugging memories: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500
