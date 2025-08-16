from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User, Setting
from app import db
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    """Main chat interface."""
    return render_template('chat.html')

@main_bp.route('/onboarding')
def onboarding():
    """Onboarding wizard for first-time users."""
    if current_user.is_authenticated:
        # Check if user has completed onboarding
        has_settings = Setting.query.filter_by(user_id=current_user.id).first()
        if has_settings:
            return redirect(url_for('main.index'))
    
    return render_template('onboarding.html')

@main_bp.route('/onboarding', methods=['POST'])
def onboarding_complete():
    """Complete onboarding process."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    # Validate CSRF token
    try:
        validate_csrf(request.form.get('csrf_token'))
    except BadRequest:
        flash('CSRF token validation failed. Please try again.', 'error')
        return redirect(url_for('main.onboarding'))
    
    # Save user profile
    current_user.name = request.form.get('name', '')
    current_user.timezone = request.form.get('timezone', 'UTC')
    current_user.bio = request.form.get('bio', '')
    
    # Save default settings
    settings_data = {
        'ollama_url': request.form.get('ollama_url', 'http://ollama:11434'),
        'ollama_model': request.form.get('ollama_model', 'llama3.1:8b'),
        'tts_url': request.form.get('tts_url', 'http://opentts:5500'),
        'tts_voice': request.form.get('tts_voice', 'en_US-amy-low'),
        'personality': request.form.get('personality', 'You are a helpful and friendly AI companion.'),
        'memory_enabled': request.form.get('memory_enabled', 'true')
    }
    
    for key, value in settings_data.items():
        setting = Setting.query.filter_by(user_id=current_user.id, key=key).first()
        if not setting:
            setting = Setting(user_id=current_user.id, key=key)
        
        # Encrypt sensitive settings
        encrypt = key in ['ollama_url', 'tts_url']
        setting.set_value(value, encrypt=encrypt)
        db.session.add(setting)
    
    db.session.commit()
    flash('Onboarding completed successfully!', 'success')
    return redirect(url_for('main.index'))
