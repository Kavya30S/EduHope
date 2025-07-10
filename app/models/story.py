from app import db
from datetime import datetime
import json

class Story(db.Model):
    __tablename__ = "stories"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    genre = db.Column(db.String(50), default="adventure")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    creator = db.relationship("User", backref="stories")
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "creator_id": self.creator_id,
            "genre": self.genre,
            "created_at": self.created_at.isoformat()
        }
    
    def get_intro(self):
        return f"🌟 Get ready for {self.title} - a {self.genre} tale!"