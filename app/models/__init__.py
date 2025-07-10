from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .achievement import Achievement, UserAchievement
from .chat import ChatSession, ChatMessage
from .CounselorConversation import CounselorConversation
from .emotion import EmotionalState
from .game_progress import GameProgress
from .journalEntry import JournalEntry
from .lesson import Lesson
from .pet_accessory import PetAccessory
from .pet import Pet
from .social import Social
from .story import Story
from .user import User

def init_db(app):
    """
    Initialize the database with the Flask app.
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Seed initial data if needed
        if not Achievement.query.first():
            for ach in Achievement.create_default_achievements():
                db.session.add(Achievement(**ach))
            db.session.commit()

# Define UserProgress for relationships
class UserProgress(db.Model):
    __tablename__ = "user_progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id"), nullable=False)
    score = db.Column(db.Integer, default=0)
    time_spent = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="progress")
    lesson = db.relationship("Lesson", backref="user_progress")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "lesson_id": self.lesson_id,
            "score": self.score,
            "time_spent": self.time_spent,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }