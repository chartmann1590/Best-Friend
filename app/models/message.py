from app import db
from datetime import datetime

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    conversation_id = db.Column(db.String(50), nullable=True)  # For grouping messages
    message_metadata = db.Column(db.JSON, default={})  # Store additional info like audio duration, etc.
    
    def to_dict(self):
        """Convert message to dictionary for API responses."""
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'conversation_id': self.conversation_id,
            'metadata': self.message_metadata
        }
