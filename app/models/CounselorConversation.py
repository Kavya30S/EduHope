from app import db
from datetime import datetime
import json

class CounselorConversation(db.Model):
    __tablename__ = "counselor_conversations"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    counselor_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    mood_detected = db.Column(db.String(20))
    
    user = db.relationship("User", backref="counselor_conversations")
    
    def __init__(self, user_id, user_message, counselor_response):
        self.user_id = user_id
        self.user_message = user_message
        self.counselor_response = counselor_response
        self.detect_mood()
    
    def detect_mood(self):
        positive = ["happy", "good", "great"]
        negative = ["sad", "bad", "upset"]
        msg_lower = self.user_message.lower()
        self.mood_detected = "happy" if any(p in msg_lower for p in positive) else "sad" if any(n in msg_lower for n in negative) else "neutral"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_message": self.user_message,
            "counselor_response": self.counselor_response,
            "timestamp": self.timestamp.isoformat(),
            "mood_detected": self.mood_detected
        }
    
    def get_child_friendly_response(self):
        responses = {
            "happy": f"🌟 Yay! {self.counselor_response}",
            "sad": f"💙 Don’t worry! {self.counselor_response}",
            "neutral": f"😊 {self.counselor_response}"
        }
        return responses.get(self.mood_detected, self.counselor_response)