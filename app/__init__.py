from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_migrate import Migrate
import os
from datetime import timedelta

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'eduhope-secret-key-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///eduhope.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.auth import auth
    from app.routes.dashboard import dashboard
    from app.routes.education import education
    from app.routes.pet_companion import pet
    from app.routes.storytelling import storytelling
    from app.routes.language_games import language_games
    from app.routes.social import social
    from app.routes.support import support
    from app.routes.api import api
    
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(dashboard, url_prefix='/dashboard')
    app.register_blueprint(education, url_prefix='/education')
    app.register_blueprint(pet, url_prefix='/pet')
    app.register_blueprint(storytelling, url_prefix='/story')
    app.register_blueprint(language_games, url_prefix='/language')
    app.register_blueprint(social, url_prefix='/social')
    app.register_blueprint(support, url_prefix='/support')
    app.register_blueprint(api, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default achievements if they don't exist
        from app.models.achievement import Achievement
        default_achievements = [
            {'name': 'First Login', 'description': 'Welcome to EduHope!', 'points': 10, 'icon': '🎉'},
            {'name': 'Pet Owner', 'description': 'Adopted your first pet!', 'points': 25, 'icon': '🐾'},
            {'name': 'Learning Streak', 'description': 'Completed lessons for 3 days in a row', 'points': 50, 'icon': '🔥'},
            {'name': 'Story Teller', 'description': 'Created your first story', 'points': 30, 'icon': '📚'},
            {'name': 'Language Explorer', 'description': 'Completed your first language game', 'points': 35, 'icon': '🌍'},
            {'name': 'Pet Caretaker', 'description': 'Fed your pet 10 times', 'points': 40, 'icon': '❤️'},
            {'name': 'Quiz Master', 'description': 'Scored 100% on a quiz', 'points': 60, 'icon': '🏆'},
            {'name': 'Social Butterfly', 'description': 'Made 5 friends', 'points': 45, 'icon': '🦋'},
        ]
        
        for ach_data in default_achievements:
            if not Achievement.query.filter_by(name=ach_data['name']).first():
                achievement = Achievement(**ach_data)
                db.session.add(achievement)
        
        db.session.commit()
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app