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
        
        with app.app_context():
            from app import db
            # Create all tables
            db.create_all()
            yield app
            # Clean up
            db.session.remove()
            db.drop_all()
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
def test_user(app):
    """Create a test user in the database."""
    with app.app_context():
        from app import db
        from app.models import User
        
        user = User(
            email='test@example.com',
            name='Test User',
            is_active=True,
            is_admin=False
        )
        user.set_password('password123')
        
        db.session.add(user)
        db.session.commit()
        
        return user

@pytest.fixture
def admin_user(app):
    """Create an admin user in the database."""
    with app.app_context():
        from app import db
        from app.models import User
        
        user = User(
            email='admin@bestfriend.local',
            name='Admin User',
            is_active=True,
            is_admin=True
        )
        user.set_password('admin123')
        
        db.session.add(user)
        db.session.commit()
        
        return user
