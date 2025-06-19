from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    language = db.Column(db.String(20), default='English')
    points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    lessons_completed = db.Column(db.Integer, default=0)
    emotional_state = db.Column(db.String(20), default='happy')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    streak_days = db.Column(db.Integer, default=0)
    
    # Relationships
    pet = db.relationship('Pet', backref='owner', uselist=False)
    achievements = db.relationship('Achievement', backref='user', lazy='dynamic')
    stories = db.relationship('Story', backref='author', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_id(self):
        return str(self.id)
    
    def add_points(self, points):
        """Add points to user and check for level up"""
        self.points += points
        
        # Level up logic
        points_for_next_level = self.level * 100
        if self.points >= points_for_next_level:
            self.level += 1
            return True  # Leveled up
        return False
    
    def get_progress_to_next_level(self):
        """Get progress percentage to next level"""
        points_needed = self.level * 100
        if self.points >= points_needed:
            return 100
        return (self.points / points_needed) * 100
    
    def update_streak(self):
        """Update daily streak"""
        today = datetime.utcnow().date()
        if self.last_login:
            last_login_date = self.last_login.date()
            if (today - last_login_date).days == 1:
                self.streak_days += 1
            elif (today - last_login_date).days > 1:
                self.streak_days = 1
        else:
            self.streak_days = 1
        
        self.last_login = datetime.utcnow()
    
    def to_dict(self):
        """Convert user to dictionary for JSON responses"""
        return {
            'id': self.id,
            'username': self.username,
            'age': self.age,
            'language': self.language,
            'points': self.points,
            'level': self.level,
            'lessons_completed': self.lessons_completed,
            'emotional_state': self.emotional_state,
            'streak_days': self.streak_days,
            'pet': self.pet.to_dict() if self.pet else None
        }