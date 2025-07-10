from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

class User(UserMixin, db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    role = db.Column(db.String(20), default="student")
    total_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    experience_points = db.Column(db.Integer, default=0)
    learning_streak = db.Column(db.Integer, default=0)
    total_lessons_completed = db.Column(db.Integer, default=0)
    total_time_spent = db.Column(db.Integer, default=0)
    learning_weights = db.Column(db.Text, default='{"visual": 0.5, "auditory": 0.3, "kinesthetic": 0.2}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_preferred_subjects(self):
        return ["math", "science", "language"]  # Placeholder
    
    def get_dominant_learning_style(self):
        weights = json.loads(self.learning_weights)
        return max(weights, key=weights.get)
    
    def adjust_learning_weights(self, style, adjustment):
        weights = json.loads(self.learning_weights)
        weights[style] = max(0, min(1, weights[style] + adjustment))
        total = sum(weights.values())
        for k in weights:
            weights[k] /= total
        self.learning_weights = json.dumps(weights)
    
    def get_stats(self):
        return {
            "total_points": self.total_points,
            "level": self.level,
            "experience_points": self.experience_points,
            "learning_streak": self.learning_streak,
            "total_lessons_completed": self.total_lessons_completed,
            "total_time_spent": self.total_time_spent
        }
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "age": self.age,
            "role": self.role,
            "stats": self.get_stats()
        }