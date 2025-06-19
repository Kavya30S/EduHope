from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    min_age = db.Column(db.Integer, default=5)
    max_age = db.Column(db.Integer, default=15)
    difficulty = db.Column(db.Integer, default=1)  # 1-5 scale
    points_reward = db.Column(db.Integer, default=50)
    
    # Interactive content
    questions = db.Column(db.Text)  # JSON string of quiz questions
    activities = db.Column(db.Text)  # JSON string of activities
    
    # Media
    image_url = db.Column(db.String(200))
    video_url = db.Column(db.String(200))
    audio_url = db.Column(db.String(200))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Pet interaction
    pet_bonus_subject = db.Column(db.String(50))  # Subject that gives pet bonus
    
    def __repr__(self):
        return f'<Lesson {self.title}>'
    
    def get_questions(self):
        """Get parsed questions from JSON"""
        if self.questions:
            try:
                return json.loads(self.questions)
            except:
                return []
        return []
    
    def set_questions(self, questions_list):
        """Set questions as JSON string"""
        self.questions = json.dumps(questions_list)
    
    def get_activities(self):
        """Get parsed activities from JSON"""
        if self.activities:
            try:
                return json.loads(self.activities)
            except:
                return []
        return []
    
    def set_activities(self, activities_list):
        """Set activities as JSON string"""
        self.activities = json.dumps(activities_list)
    
    def is_suitable_for_age(self, age):
        """Check if lesson is suitable for given age"""
        return self.min_age <= age <= self.max_age
    
    def get_pet_bonus(self, pet_type):
        """Get bonus points if pet type matches lesson subject"""
        pet_subject_bonuses = {
            'dragon': 'Math',
            'unicorn': 'English',
            'robot': 'Science',
            'phoenix': 'History',
            'cat': 'Art'
        }
        
        if pet_subject_bonuses.get(pet_type) == self.subject:
            return int(self.points_reward * 0.2)  # 20% bonus
        return 0
    
    def to_dict(self):
        """Convert lesson to dictionary for JSON responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'subject': self.subject,
            'min_age': self.min_age,
            'max_age': self.max_age,
            'difficulty': self.difficulty,
            'points_reward': self.points_reward,
            'questions': self.get_questions(),
            'activities': self.get_activities(),
            'image_url': self.image_url,
            'video_url': self.video_url,
            'audio_url': self.audio_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }