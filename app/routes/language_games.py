from flask import Blueprint, render_template, request
from flask_login import login_required
from app.services.voice_service import VoiceService
from app import socketio

bp = Blueprint('language_games', __name__)
voice_service = VoiceService()

@bp.route('/language_games', methods=['GET', 'POST'])
@login_required
def language_games():
    if request.method == 'POST':
        user_audio = request.files['audio']
        recognized_text = voice_service.speech_to_text(user_audio)
        expected_phrase = "Hello, how are you?"  # Example phrase
        score = 1 if recognized_text.lower() == expected_phrase.lower() else 0
        socketio.emit('game_update', {'score': score}, room=str(current_user.id))
        return render_template('language_game.html', score=score)
    return render_template('language_game.html')