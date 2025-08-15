from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Setting
from app import db

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
    settings_data = request.form.to_dict()
    
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
