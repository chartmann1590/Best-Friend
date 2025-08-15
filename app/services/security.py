import os
from cryptography.fernet import Fernet
from flask import current_app

class SecurityService:
    def __init__(self, app):
        self.app = app
        self.fernet = None
        self._init_fernet()
    
    def _init_fernet(self):
        """Initialize Fernet cipher for encryption."""
        key = self.app.config.get('FERNET_KEY')
        if not key:
            raise ValueError("FERNET_KEY not configured")
        
        # Ensure key is properly formatted
        if len(key) != 44:  # Base64 encoded 32-byte key
            raise ValueError("FERNET_KEY must be a 32-byte base64-encoded string")
        
        self.fernet = Fernet(key.encode())
    
    def encrypt_value(self, value):
        """Encrypt a string value."""
        if not value:
            return value
        return self.fernet.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value):
        """Decrypt an encrypted string value."""
        if not encrypted_value:
            return encrypted_value
        try:
            return self.fernet.decrypt(encrypted_value.encode()).decode()
        except Exception:
            return None

def encrypt_value(value):
    """Global function to encrypt values."""
    return current_app.security_service.encrypt_value(value)

def decrypt_value(encrypted_value):
    """Global function to decrypt values."""
    return current_app.security_service.decrypt_value(encrypted_value)
