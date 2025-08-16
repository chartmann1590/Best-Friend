import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://bestfriend:bestfriend@localhost:5432/bestfriend'
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Ollama Configuration (Remote)
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL') or 'http://your-ollama-server:11434'
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL') or 'llama3.1:8b'
    EMBED_MODEL = os.environ.get('EMBED_MODEL') or 'nomic-embed-text'
    
    # TTS Configuration
    TTS_URL = os.environ.get('TTS_URL') or 'http://localhost:5500'
    TTS_VOICE = os.environ.get('TTS_VOICE') or 'en_US-amy-low'
    
    # STT Configuration
    STT_LANGUAGE = os.environ.get('STT_LANGUAGE') or 'en'
    
    # Security
    FERNET_KEY = os.environ.get('FERNET_KEY')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Rate Limiting
    RATE_LIMIT_PER_IP = int(os.environ.get('RATE_LIMIT_PER_IP', 100))
    RATE_LIMIT_PER_USER = int(os.environ.get('RATE_LIMIT_PER_USER', 50))
    
    # Admin Configuration
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@bestfriend.local'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://bestfriend:bestfriend@localhost:5432/bestfriend_dev'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://bestfriend:bestfriend@localhost:5432/bestfriend_test'
    WTF_CSRF_ENABLED = False
    
    # Test-specific security keys (32-byte base64-encoded)
    # This is a valid base64-encoded 32-byte key for testing only
    FERNET_KEY = 'if9rlP7+8WlMsXPdmS7M7/dKzGeQM295muBhQ+HnyAY='
    SECRET_KEY = 'dGVzdC1zZWNyZXQta2V5LXRlc3Rpbmctb25seS1ub3QtcHJvZHVjdGlvbg=='
    
    # Test-specific service configurations
    OLLAMA_BASE_URL = 'http://localhost:11434'  # Mock URL for testing
    TTS_URL = 'http://localhost:5500'  # Mock URL for testing
    REDIS_URL = 'redis://localhost:6379/0'  # Test Redis instance
