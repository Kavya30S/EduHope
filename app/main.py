from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_babel import Babel
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from utils.helpers import load_config
import os

app = Flask(__name__)
app.config.update(load_config('config.json'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key-for-kids')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')
app.config['BABEL_DEFAULT_LOCALE'] = 'en'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
socketio = SocketIO(app, cors_allowed_origins="*")
babel = Babel(app)
cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://localhost:6379/0'})
limiter = Limiter(app, key_func=get_remote_address)
mail = Mail(app)

# Register blueprints
from app.routes import auth, education, support, social, teacher, pet_companion, storytelling, language_games, assessment
app.register_blueprint(auth.auth_bp)
app.register_blueprint(education.education_bp)
app.register_blueprint(support.support_bp)
app.register_blueprint(social.social_bp)
app.register_blueprint(teacher.teacher_bp)
app.register_blueprint(pet_companion.pet_companion_bp)
app.register_blueprint(storytelling.storytelling_bp)
app.register_blueprint(language_games.language_games_bp)
app.register_blueprint(assessment.assessment_bp)

# Initialize database
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))

# Error handling
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Context processor for child-friendly UI
@app.context_processor
def utility_processor():
    def get_emoji(mood: str) -> str:
        from utils.helpers import generate_child_friendly_message
        return generate_child_friendly_message(mood)
    return dict(get_emoji=get_emoji)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)