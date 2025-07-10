from app import db
from datetime import datetime
import json

class Lesson(db.Model):
    __tablename__ = "lessons"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    difficulty_level = db.Column(db.Integer, default=1)
    style = db.Column(db.String(50), default="visual")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "subject": self.subject,
            "content": self.content,
            "difficulty_level": self.difficulty_level,
            "style": self.style,
            "created_at": self.created_at.isoformat()
        }
    
    def get_child_friendly_description(self):
        desc = {
            "math": "🧮 Fun with numbers!",
            "science": "🔬 Explore cool stuff!",
            "language": "📚 Words are magic!"
        }
        return desc.get(self.subject.lower(), f"🌟 Learn {self.subject}!")