from flask import Blueprint, render_template, request, redirect, url_for
015from flask_login import login_required, current_user
from app import db

bp = Blueprint('assessment_games', __name__)

@bp.route('/knowledge_assessment', methods=['GET', 'POST'])
@login_required
def knowledge_assessment():
    if request.method == 'POST':
        answers = request.form.getlist('answer')
        score = sum(1 for ans in answers if ans == 'correct')  # Simplified scoring
        current_user.knowledge_level = score * 10
        db.session.commit()
        return redirect(url_for('assessment_games.emotional_assessment'))
    questions = [{'id': 1, 'text': '2 + 2 = ?', 'options': ['3', '4', '5'], 'correct': '4'}]
    return render_template('knowledge_assessment.html', questions=questions)