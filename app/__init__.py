from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'edu-hope-secret-2023'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///edu_hope.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    socketio.init_app(app)

    # Register blueprints for routes
    from app.routes import auth, pet_companion, storytelling, language_games
    from app.assessment_games import bp as assessment_bp
    app.register_blueprint(auth.bp)
    app.register_blueprint(pet_companion.bp)
    app.register_blueprint(storytelling.bp)
    app.register_blueprint(language_games.bp)
    app.register_blueprint(assessment_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app, socketio

# Create app and socketio instances
app, socketio = create_app()

# Run the app with SocketIO if this is the main module
if __name__ == '__main__':
    socketio.run(app, debug=True)