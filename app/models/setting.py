from app import db
from datetime import datetime
from app.services.security import encrypt_value, decrypt_value

class Setting(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=True)
    is_encrypted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'key', name='_user_setting_uc'),)
    
    def set_value(self, value, encrypt=False):
        """Set value, optionally encrypting it."""
        if encrypt:
            self.value = encrypt_value(value)
            self.is_encrypted = True
        else:
            self.value = value
            self.is_encrypted = False
    
    def get_value(self):
        """Get value, decrypting if necessary."""
        if self.is_encrypted and self.value:
            return decrypt_value(self.value)
        return self.value
    
    def to_dict(self):
        """Convert setting to dictionary for API responses."""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.get_value(),
            'is_encrypted': self.is_encrypted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
