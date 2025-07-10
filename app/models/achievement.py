from app import db
from datetime import datetime
import json

class Achievement(db.Model):
    __tablename__ = "achievements"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(100), default="🏆")
    color = db.Column(db.String(7), default="#FFD700")
    requirements = db.Column(db.Text)
    points_required = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "color": self.color,
            "requirements": json.loads(self.requirements) if self.requirements else {}
        }
    
    def check_requirements(self, stats):
        reqs = json.loads(self.requirements) if self.requirements else {}
        return all(stats.get(k, 0) >= v for k, v in reqs.items()) and stats.get("total_points", 0) >= self.points_required

    @staticmethod
    def create_default_achievements():
        return [
            {
                "name": "First Lesson",
                "description": "Complete your first lesson!",
                "category": "learning",
                "icon": "📚",
                "color": "#4CAF50",
                "requirements": json.dumps({"total_lessons_completed": 1}),
                "points_required": 50
            },
            {
                "name": "Pet Friend",
                "description": "Care for your pet 5 times!",
                "category": "pet_care",
                "icon": "🐾",
                "color": "#E91E63",
                "requirements": json.dumps({"pet_interactions": 5}),
                "points_required": 100
            }
        ]

class UserAchievement(db.Model):
    __tablename__ = "user_achievements"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey("achievements.id"), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    achievement = db.relationship("Achievement", backref="user_achievements")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "achievement": self.achievement.to_dict(),
            "earned_at": self.earned_at.isoformat()
        }