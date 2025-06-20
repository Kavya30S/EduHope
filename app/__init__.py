from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
import os

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'eduhope-super-secret-key-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///eduhope.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False  # For mobile app compatibility
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '🌟 Please log in to access your magical learning world!'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.education import education_bp
    from app.routes.support import support_bp
    from app.routes.pet_companion import pet_bp
    from app.routes.social import social_bp
    from app.routes.teacher import teacher_bp
    from app.routes.storytelling import storytelling_bp
    from app.routes.language_games import language_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(education_bp)
    app.register_blueprint(support_bp)
    app.register_blueprint(pet_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(storytelling_bp)
    app.register_blueprint(language_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Initialize default data
        from app.models.pet import PetType
        from app.models.lesson import Subject
        
        # Create default pet types if they don't exist
        if not PetType.query.first():
            pet_types = [
                {'name': 'Dragon', 'description': 'A magical fire-breathing companion', 'emoji': '🐉'},
                {'name': 'Unicorn', 'description': 'A mystical rainbow friend', 'emoji': '🦄'},
                {'name': 'Phoenix', 'description': 'A beautiful bird of rebirth', 'emoji': '🔥'},
                {'name': 'Griffin', 'description': 'A majestic eagle-lion hybrid', 'emoji': '🦅'},
                {'name': 'Fairy', 'description': 'A tiny magical helper', 'emoji': '🧚'},
                {'name': 'Robot', 'description': 'A futuristic AI companion', 'emoji': '🤖'},
                {'name': 'Alien', 'description': 'A friendly space visitor', 'emoji': '👽'},
                {'name': 'Mermaid', 'description': 'An ocean princess', 'emoji': '🧜'},
                {'name': 'Wizard', 'description': 'A wise magic master', 'emoji': '🧙'},
                {'name': 'Angel', 'description': 'A heavenly guardian', 'emoji': '😇'},
                {'name': 'Butterfly', 'description': 'A colorful flying friend', 'emoji': '🦋'},
                {'name': 'Tiger', 'description': 'A brave jungle guardian', 'emoji': '🐅'},
                {'name': 'Panda', 'description': 'A cuddly bamboo lover', 'emoji': '🐼'},
                {'name': 'Owl', 'description': 'A wise night companion', 'emoji': '🦉'},
                {'name': 'Fox', 'description': 'A clever forest friend', 'emoji': '🦊'},
                {'name': 'Dolphin', 'description': 'A playful ocean buddy', 'emoji': '🐬'},
                {'name': 'Pegasus', 'description': 'A winged horse of dreams', 'emoji': '🐴'},
                {'name': 'Crystal Bear', 'description': 'A shimmering magical bear', 'emoji': '💎'},
                {'name': 'Star Cat', 'description': 'A cosmic feline friend', 'emoji': '⭐'},
                {'name': 'Rainbow Bird', 'description': 'A colorful sky dancer', 'emoji': '🌈'},
                {'name': 'Moon Wolf', 'description': 'A mysterious lunar companion', 'emoji': '🌙'},
                {'name': 'Sun Lion', 'description': 'A radiant golden protector', 'emoji': '☀️'},
            ]
            
            for pet_data in pet_types:
                pet_type = PetType(**pet_data)
                db.session.add(pet_type)
        
        # Create default subjects
        if not Subject.query.first():
            subjects = [
                {'name': 'Mathematics', 'description': 'Numbers and problem solving', 'color': '#FF6B6B'},
                {'name': 'Science', 'description': 'Discover the world around us', 'color': '#4ECDC4'},
                {'name': 'Language Arts', 'description': 'Reading and writing adventures', 'color': '#45B7D1'},
                {'name': 'History', 'description': 'Stories from the past', 'color': '#FFA07A'},
                {'name': 'Geography', 'description': 'Explore our amazing planet', 'color': '#98D8C8'},
                {'name': 'Art', 'description': 'Express your creativity', 'color': '#F7DC6F'},
                {'name': 'Music', 'description': 'Rhythm and melody fun', 'color': '#BB8FCE'},
                {'name': 'Life Skills', 'description': 'Important everyday knowledge', 'color': '#85C1E9'},
            ]
            
            for subject_data in subjects:
                subject = Subject(**subject_data)
                db.session.add(subject)
        
        db.session.commit()
    
    return app