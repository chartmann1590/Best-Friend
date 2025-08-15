import pytest
from app.models import User
from app import db

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/healthz/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'services' in data

def test_login_page(client):
    """Test login page accessibility."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Sign in to your account' in response.data

def test_create_admin(app, runner):
    """Test admin user creation."""
    with app.app_context():
        result = runner.invoke(['create-admin'])
        assert result.exit_code == 0
        
        # Check if admin user was created
        admin = User.query.filter_by(email='admin@bestfriend.local').first()
        assert admin is not None
        assert admin.is_admin == True

def test_user_model(app):
    """Test user model functionality."""
    with app.app_context():
        user = User(
            email='test@example.com',
            name='Test User'
        )
        user.set_password('password123')
        
        db.session.add(user)
        db.session.commit()
        
        # Test password verification
        assert user.check_password('password123') == True
        assert user.check_password('wrongpassword') == False
        
        # Test user serialization
        user_dict = user.to_dict()
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['name'] == 'Test User'
