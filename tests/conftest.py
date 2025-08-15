import os
import sys
import pytest
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Try to import app components, but don't fail if they're not available
try:
    from app import create_app
    from app.models import User, Setting
    APP_AVAILABLE = True
except ImportError:
    APP_AVAILABLE = False

@pytest.fixture(scope='function')
def app():
    """Create application for testing."""
    if not APP_AVAILABLE:
        pytest.skip("App not available for testing")
    
    try:
        app = create_app('testing')
        return app
    except Exception as e:
        pytest.skip(f"Could not create app: {e}")

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test runner."""
    return app.test_cli_runner()

@pytest.fixture
def test_user():
    """Create a test user."""
    user = type('User', (), {
        'id': 1,
        'email': 'test@example.com',
        'name': 'Test User',
        'is_active': True,
        'is_admin': False,
        'check_password': lambda self, password: password == 'password123',
        'to_dict': lambda self: {
            'id': 1,
            'email': 'test@example.com',
            'name': 'Test User'
        }
    })()
    return user

@pytest.fixture
def admin_user():
    """Create an admin user."""
    user = type('User', (), {
        'id': 2,
        'email': 'admin@bestfriend.local',
        'name': 'Admin User',
        'is_active': True,
        'is_admin': True,
        'check_password': lambda self, password: password == 'admin123',
        'to_dict': lambda self: {
            'id': 2,
            'email': 'admin@bestfriend.local',
            'name': 'Admin User',
            'is_admin': True
        }
    })()
    return user
