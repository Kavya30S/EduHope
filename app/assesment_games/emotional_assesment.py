from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app import db

@bp = Blueprint('assessment_games', __name__)

@bp.route('/emotional_assessment', methods=['GET', 'POST'])
@login_required
def emotional_assessment():
    if request.method == 'POST':
        mood = request.form.get('mood', 'neutral')
        current_user.emotional_state = mood
        current_user.assessment_completed = True
        db.session.commit()
        return redirect(url_for('education.dashboard'))
    return render_template('emotional_assessment.html')