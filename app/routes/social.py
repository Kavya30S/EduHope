from flask_socketio import emit

@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True);from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('social', __name__)

@bp.route('/chat')
@login_required
def chat():
    return render_template('chat.html')