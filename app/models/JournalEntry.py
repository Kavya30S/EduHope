from app import db
from datetime import datetime
import json

class JournalEntry(db.Model):
    __tablename__ = "journal_entries"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(255), default="My Day")
    content = db.Column(db.Text, nullable=False)
    mood = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    stickers = db.Column(db.Text, default="[]")
    
    user = db.relationship("User", backref="journal_entries")
    
    def get_stickers(self):
        return json.loads(self.stickers)
    
    def add_sticker(self, sticker):
        stickers = self.get_stickers()
        if sticker not in stickers:
            stickers.append(sticker)
            self.stickers = json.dumps(stickers)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content,
            "mood": self.mood,
            "timestamp": self.timestamp.isoformat(),
            "stickers": self.get_stickers()
        }
    
    def get_summary(self):
        return f"🌟 {self.title}: {self.content[:50]}..."