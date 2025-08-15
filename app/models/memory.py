from app import db
from datetime import datetime
from pgvector.sqlalchemy import Vector

class Memory(db.Model):
    __tablename__ = 'memories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(Vector(384), nullable=True)  # Default embedding dimension
    memory_type = db.Column(db.String(50), default='conversation')  # conversation, fact, preference, etc.
    importance = db.Column(db.Float, default=1.0)  # 0.0 to 1.0
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    metadata = db.Column(db.JSON, default={})
    
    def to_dict(self):
        """Convert memory to dictionary for API responses."""
        return {
            'id': self.id,
            'content': self.content,
            'memory_type': self.memory_type,
            'importance': self.importance,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.metadata
        }
