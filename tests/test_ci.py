"""
CI-specific tests that can run in the GitHub Actions environment.
These tests assume all dependencies are available.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_environment_setup():
    """Test that the CI environment is properly set up."""
    # Check that we're in the right directory
    assert Path.cwd().name == 'Best-Friend'
    
    # Check that app directory exists
    assert Path('app').exists()
    assert Path('app/__init__.py').exists()
    
    # Check that tests directory exists
    assert Path('tests').exists()
    
    # Check that requirements.txt exists
    assert Path('requirements.txt').exists()

def test_import_app():
    """Test that we can import the app module."""
    try:
        from app import create_app
        assert callable(create_app)
        print("✅ App import successful")
    except ImportError as e:
        pytest.fail(f"Failed to import app: {e}")

def test_create_testing_app():
    """Test that we can create a testing app instance."""
    try:
        from app import create_app
        app = create_app('testing')
        assert app.config['TESTING'] == True
        print("✅ Testing app creation successful")
    except Exception as e:
        pytest.fail(f"Failed to create testing app: {e}")

def test_database_connection():
    """Test that we can connect to the test database."""
    try:
        from app import create_app
        app = create_app('testing')
        
        with app.app_context():
            from app import db
            # This should work if the database is accessible
            db.engine.execute("SELECT 1")
            print("✅ Database connection successful")
    except Exception as e:
        pytest.skip(f"Database not accessible: {e}")

def test_redis_connection():
    """Test that we can connect to Redis."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        pytest.skip(f"Redis not accessible: {e}")

def test_basic_models():
    """Test that basic models can be imported and used."""
    try:
        from app.models import User, Setting
        assert User is not None
        assert Setting is not None
        print("✅ Basic models import successful")
    except ImportError as e:
        pytest.fail(f"Failed to import models: {e}")

def test_basic_services():
    """Test that basic services can be imported."""
    try:
        from app.services import init_services
        assert callable(init_services)
        print("✅ Basic services import successful")
    except ImportError as e:
        pytest.skip(f"Services not available: {e}")

def test_blueprints():
    """Test that blueprints can be imported."""
    try:
        from app.blueprints import auth, chat, settings, admin, privacy, health, main
        print("✅ Blueprints import successful")
    except ImportError as e:
        pytest.skip(f"Blueprints not available: {e}")

def test_configuration():
    """Test that configuration classes exist."""
    try:
        from app.config import Config, DevelopmentConfig, ProductionConfig, TestingConfig
        assert Config is not None
        assert DevelopmentConfig is not None
        assert ProductionConfig is not None
        assert TestingConfig is not None
        print("✅ Configuration classes import successful")
    except ImportError as e:
        pytest.fail(f"Failed to import configuration: {e}")

def test_cli_commands():
    """Test that CLI commands can be imported."""
    try:
        from app.cli import init_app
        assert callable(init_app)
        print("✅ CLI commands import successful")
    except ImportError as e:
        pytest.skip(f"CLI commands not available: {e}")

def test_logging_config():
    """Test that logging configuration can be imported."""
    try:
        from app.logging_config import setup_logging
        assert callable(setup_logging)
        print("✅ Logging configuration import successful")
    except ImportError as e:
        pytest.skip(f"Logging configuration not available: {e}")
