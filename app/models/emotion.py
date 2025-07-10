from app import db
from datetime import datetime
import json

class EmotionalState(db.Model):
    __tablename__ = "emotional_states"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    happiness = db.Column(db.Float, default=50.0)
    stress_level = db.Column(db.Float, default=30.0)
    recent_moods = db.Column(db.Text, default="[]")
    last_check_in = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship("User", backref="emotional_state")
    
    def get_recent_moods(self):
        return json.loads(self.recent_moods)
    
    def add_mood_entry(self, mood_data):
        moods = self.get_recent_moods()
        moods.append({
            "timestamp": datetime.utcnow().isoformat(),
            "mood": mood_data["mood"],
            "intensity": mood_data["intensity"]
        })
        self.recent_moods = json.dumps(moods[-50:])
        self.update_metrics(mood_data)
    
    def update_metrics(self, mood_data):
        mood = mood_data["mood"]
        intensity = mood_data["intensity"]
        if mood == "happy":
            self.happiness = min(100, self.happiness + intensity)
        elif mood == "sad":
            self.happiness = max(0, self.happiness - intensity)
        elif mood == "anxious":
            self.stress_level = min(100, self.stress_level + intensity)
        self.last_check_in = datetime.utcnow()
    
    def to_dict(self):
        return {
            "happiness": self.happiness,
            "stress_level": self.stress_level,
            "recent_moods": self.get_recent_moods(),
            "last_check_in": self.last_check_in.isoformat()
        }
    
    def get_emotional_summary(self):
        avg = (self.happiness + (100 - self.stress_level)) / 2
        return {"score": avg, "state": "Good" if avg > 50 else "Okay"}