from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
from werkzeug.security import check_password_hash
from app.logging_config import log_authentication_event, log_security_event, log_error
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            
            # Log successful login
            log_authentication_event(
                'login',
                user.id,
                request.remote_addr,
                True,
                f"User agent: {request.headers.get('User-Agent', 'Unknown')}"
            )
            
            return redirect(next_page or url_for('main.index'))
        else:
            # Log failed login attempt
            log_authentication_event(
                'login',
                email,
                request.remote_addr,
                False,
                f"Invalid credentials for email: {email}"
            )
            
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    # Log logout event
    log_authentication_event(
        'logout',
        current_user.id,
        request.remote_addr,
        True,
        f"User agent: {request.headers.get('User-Agent', 'Unknown')}"
    )
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password."""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            log_security_event(
                'password_change_failed',
                f"Current password incorrect for user {current_user.id}",
                current_user.id,
                request.remote_addr
            )
            flash('Current password is incorrect', 'error')
        elif new_password != confirm_password:
            log_security_event(
                'password_change_failed',
                f"Password confirmation mismatch for user {current_user.id}",
                current_user.id,
                request.remote_addr
            )
            flash('New passwords do not match', 'error')
        elif len(new_password) < 8:
            log_security_event(
                'password_change_failed',
                f"Password too short for user {current_user.id}",
                current_user.id,
                request.remote_addr
            )
            flash('Password must be at least 8 characters long', 'error')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            
            # Log successful password change
            log_security_event(
                'password_changed',
                f"Password changed successfully for user {current_user.id}",
                current_user.id,
                request.remote_addr
            )
            
            flash('Password changed successfully', 'success')
            return redirect(url_for('main.index'))
    
    return render_template('auth/change_password.html')

@auth_bp.route('/create-admin')
def create_admin():
    """Create admin user (development only)."""
    if os.environ.get('FLASK_ENV') == 'production':
        flash('Admin creation disabled in production', 'error')
        return redirect(url_for('auth.login'))
    
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@bestfriend.local')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # Check if admin already exists
    admin = User.query.filter_by(email=admin_email).first()
    if admin:
        flash('Admin user already exists', 'info')
        return redirect(url_for('auth.login'))
    
    # Create admin user
    admin = User(
        email=admin_email,
        name='Administrator',
        is_admin=True
    )
    admin.set_password(admin_password)
    
    db.session.add(admin)
    db.session.commit()
    
    # Log admin user creation
    log_security_event(
        'admin_created',
        f"Admin user created: {admin_email}",
        None,
        request.remote_addr
    )
    
    flash(f'Admin user created: {admin_email}', 'success')
    return redirect(url_for('auth.login'))
