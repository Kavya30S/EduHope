from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from fuzzywuzzy import fuzz
from app import db
from app.models.game_progress import GameProgress
from app.services.voice_service import recognize_speech
from app.config import Config
import random

language_games_bp = Blueprint('language_games', __name__)

@language_games_bp.route('/language_games')
@login_required
def language_games():
    progress = GameProgress.query.filter_by(user_id=current_user.id, game_type='language').all()
    return render_template('language_game.html', progress=progress)

@language_games_bp.route('/language_game/play', methods=['POST'])
@login_required
def play_language_game():
    config = Config()
    dataset_path = config.get_dataset_path('who')  # Corrected to use custom_health_facts.txt
    with open(dataset_path, 'r', encoding='utf-8') as f:
        sentences = f.readlines()
    expected = random.choice(sentences).strip()
    audio_file = request.files['audio']
    spoken_text = recognize_speech(audio_file)
    similarity = fuzz.ratio(spoken_text.lower(), expected.lower())
    score = similarity if similarity > 50 else 0
    progress = GameProgress(user_id=current_user.id, game_type='language', score=score, completed=True)
    db.session.add(progress)
    db.session.commit()
    return redirect(url_for('language_games.language_games'))