from flask import Blueprint

auth_bp = Blueprint("auth", __name__)
education_bp = Blueprint("education", __name__)
language_games_bp = Blueprint("language_games", __name__)
pet_companion_bp = Blueprint("pet_companion", __name__)
social_bp = Blueprint("social", __name__)
storytelling_bp = Blueprint("storytelling", __name__)
support_bp = Blueprint("support", __name__)
teacher_bp = Blueprint("teacher", __name__)

from .auth import *
from .education import *
from .language_games import *
from .pet_companion import *
from .social import *
from .storytelling import *
from .support import *
from .teacher import *

def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(education_bp, url_prefix="/education")
    app.register_blueprint(language_games_bp, url_prefix="/games")
    app.register_blueprint(pet_companion_bp, url_prefix="/pet")
    app.register_blueprint(social_bp, url_prefix="/social")
    app.register_blueprint(storytelling_bp, url_prefix="/story")
    app.register_blueprint(support_bp, url_prefix="/support")
    app.register_blueprint(teacher_bp, url_prefix="/teacher")