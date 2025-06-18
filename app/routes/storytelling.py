from flask import Blueprint, render_template, request
from flask_login import login_required
from app.services.llm_service import LLMService
from app import socketio

bp = Blueprint('storytelling', __name__)
llm_service = LLMService()

@bp.route('/storytelling', methods=['GET', 'POST'])
@login_required
def storytelling():
    if request.method == 'POST':
        user_input = request.form['story_input']
        suggestion = llm_service.generate_suggestion(user_input)
        socketio.emit('story_update', {'input': user_input, 'suggestion': suggestion}, broadcast=True)
        return render_template('storytelling.html', suggestion=suggestion)
    return render_template('storytelling.html')