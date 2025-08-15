from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import User, Message, Memory
from app import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
def index():
    """Admin dashboard."""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    # Get system statistics
    stats = {
        'total_users': User.query.count(),
        'total_messages': Message.query.count(),
        'total_memories': Memory.query.count(),
        'active_users': User.query.filter_by(is_active=True).count()
    }
    
    return render_template('admin.html', stats=stats)

@admin_bp.route('/api/stats')
@login_required
def get_stats():
    """Get system statistics."""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    stats = {
        'total_users': User.query.count(),
        'total_messages': Message.query.count(),
        'total_memories': Memory.query.count(),
        'active_users': User.query.filter_by(is_active=True).count()
    }
    
    return jsonify(stats)
