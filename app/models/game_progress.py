from app import db
from datetime import datetime
import json

class GameProgress(db.Model):
    __tablename__ = "game_progress"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, default=1)
    score = db.Column(db.Integer, default=0)
    highest_score = db.Column(db.Integer, default=0)
    time_spent = db.Column(db.Integer, default=0)
    last_played = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship("User", backref="game_progress")
    
    def update_progress(self, score, time_spent, success=True):
        self.score = score
        self.time_spent += time_spent
        self.last_played = datetime.utcnow()
        if score > self.highest_score:
            self.highest_score = score
        if success and self.score >= self.level * 100:
            self.level += 1
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "game_type": self.game_type,
            "level": self.level,
            "score": self.score,
            "highest_score": self.highest_score,
            "time_spent": self.time_spent,
            "last_played": self.last_played.isoformat()
        }
    
    def get_child_friendly_message(self):
        return f"🎉 You’re awesome at {self.game_type} - Level {self.level}!"