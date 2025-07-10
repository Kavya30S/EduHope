from app import db
from datetime import datetime
from enum import Enum
import json

class ChatType(Enum):
    GENERAL = "general"
    SUPPORT = "support"
    EDUCATION = "education"

class ChatSession(db.Model):
    __tablename__ = "chat_sessions"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    chat_type = db.Column(db.Enum(ChatType), default=ChatType.GENERAL)
    session_name = db.Column(db.String(100))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_messages = db.Column(db.Integer, default=0)
    
    messages = db.relationship("ChatMessage", backref="session", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "chat_type": self.chat_type.value,
            "session_name": self.session_name,
            "started_at": self.started_at.isoformat(),
            "total_messages": self.total_messages
        }

class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_from_user = db.Column(db.Boolean, default=True)
    emotion_detected = db.Column(db.String(50))
    sentiment_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ai_response_type = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "content": self.content,
            "is_from_user": self.is_from_user,
            "emotion_detected": self.emotion_detected,
            "sentiment_score": self.sentiment_score,
            "created_at": self.created_at.isoformat(),
            "ai_response_type": self.ai_response_type
        }
    
    @staticmethod
    def get_user_emotion_history(user_id, days):
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        return ChatMessage.query.filter(
            ChatMessage.user_id == user_id,
            ChatMessage.created_at >= cutoff
        ).all()