from app import db
from datetime import datetime
import json

class Pet(db.Model):
    __tablename__ = "pets"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    pet_type = db.Column(db.String(50), nullable=False)
    happiness = db.Column(db.Integer, default=50)
    hunger = db.Column(db.Integer, default=50)
    energy = db.Column(db.Integer, default=100)
    last_fed = db.Column(db.DateTime, default=datetime.utcnow)
    last_played = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship("User", backref="pets")
    
    def feed(self):
        self.hunger = max(0, self.hunger - 30)
        self.happiness = min(100, self.happiness + 10)
        self.last_fed = datetime.utcnow()
        return f"🍽️ {self.name} is full and happy!"
    
    def play(self):
        if self.energy >= 10:
            self.energy -= 10
            self.happiness = min(100, self.happiness + 15)
            self.last_played = datetime.utcnow()
            return f"🎉 {self.name} had fun playing!"
        return f"😴 {self.name} is too tired!"
    
    def get_mood(self):
        avg = (self.happiness + self.energy + (100 - self.hunger)) / 3
        return {"mood": "Happy" if avg > 60 else "Okay" if avg > 30 else "Sad", "score": avg}
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "pet_type": self.pet_type,
            "happiness": self.happiness,
            "hunger": self.hunger,
            "energy": self.energy,
            "mood": self.get_mood(),
            "last_fed": self.last_fed.isoformat(),
            "last_played": self.last_played.isoformat()
        }