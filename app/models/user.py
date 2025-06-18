from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)  # Hashed password
    username = db.Column(db.String(20), unique=True, nullable=False)
    points = db.Column(db.Integer, default=0)  # Gamification: Earn points for activities
    assessment_completed = db.Column(db.Boolean, default=False)
    knowledge_level = db.Column(db.Integer, default=1)  # Starts at level 1
    emotional_state = db.Column(db.String(20), default='happy')  # For emotional support