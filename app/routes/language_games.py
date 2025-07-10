from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models.game_progress import GameProgress
from app.services.voice_service import recognize_speech

language_games = Blueprint("language_games", __name__)

@language_games.route("/language")
@login_required
def language_game():
    progress = GameProgress.query.filter_by(user_id=current_user.id, game_type="language").first()
    return render_template("language_game.html", progress=progress)

@language_games.route("/language/play", methods=["POST"])
@login_required
def play_language_game():
    audio = request.files["audio"]
    audio_data = AudioData(audio.read(), sample_rate=16000, sample_width=2)
    result, status = recognize_speech(audio_data)
    if status != 200:
        flash(result["error"])
        return redirect(url_for("language_games.language_game"))

    progress = GameProgress.query.filter_by(user_id=current_user.id, game_type="language").first()
    if not progress:
        progress = GameProgress(user_id=current_user.id, game_type="language")
        db.session.add(progress)
    progress.update_progress(score=100, time_spent=60, success=True)
    db.session.commit()
    flash("Great job speaking!")
    return redirect(url_for("language_games.language_game"))