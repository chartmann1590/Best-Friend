from flask import Blueprint, jsonify, send_file
from flask_login import login_required, current_user
from app.models import User, Message, Memory, Setting
from app import db
import json
import io
from datetime import datetime

privacy_bp = Blueprint('privacy', __name__)

@privacy_bp.route('/export')
@login_required
def export_data():
    """Export user data."""
    # Collect user data
    user_data = {
        'user': current_user.to_dict(),
        'messages': [msg.to_dict() for msg in current_user.messages],
        'memories': [mem.to_dict() for mem in current_user.memories],
        'settings': [setting.to_dict() for setting in current_user.settings],
        'exported_at': datetime.utcnow().isoformat()
    }
    
    # Create JSON file
    json_data = json.dumps(user_data, indent=2, default=str)
    file_buffer = io.BytesIO(json_data.encode('utf-8'))
    file_buffer.seek(0)
    
    filename = f"bestfriend_export_{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    
    return send_file(
        file_buffer,
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )

@privacy_bp.route('/delete', methods=['DELETE'])
@login_required
def delete_data():
    """Delete all user data."""
    try:
        # Delete user data (cascade will handle related records)
        db.session.delete(current_user)
        db.session.commit()
        
        return jsonify({'message': 'All data deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete data: {str(e)}'}), 500
