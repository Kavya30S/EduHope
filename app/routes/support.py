from flask import Blueprint, render_template
from flask_login import login_required
from app.services.sentiment_service import SentimentService

bp = Blueprint('support', __name__)
sentiment_service = SentimentService()

@bp.route('/support')
@login_required
def support():
    return render_template('chat.html')

@bp.route('/analyze_mood', methods=['POST'])
@login_required
def analyze_mood():
    text = request.form['message']
    mood = sentiment_service.analyze(text)
    return render_template('chat.html', mood=mood)