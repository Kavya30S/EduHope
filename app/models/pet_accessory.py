from app import db
from datetime import datetime
import json

class PetAccessory(db.Model):
    __tablename__ = "pet_accessories"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    rarity = db.Column(db.String(20), default="common")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "rarity": self.rarity,
            "created_at": self.created_at.isoformat()
        }
    
    def get_child_friendly_description(self):
        return f"✨ {self.name}: {self.description} for your pet!"