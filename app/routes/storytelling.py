from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app import db, socketio
from app.models.story import Story
from app.services.llm_services import generate_story_suggestion
from app.config import Config
import random

storytelling_bp = Blueprint('storytelling', __name__)

@storytelling_bp.route('/storytelling')
@login_required
def storytelling():
    config = Config()
    dataset_path = config.get_dataset_path('wikitext')  # Corrected to use custom_stories.txt
    with open(dataset_path, 'r', encoding='utf-8') as f:
        story_prompts = f.readlines()
    random_prompt = random.choice(story_prompts) if story_prompts else "Once upon a time..."
    stories = Story.query.all()
    return render_template('storytelling.html', stories=stories, random_prompt=random_prompt)

@storytelling_bp.route('/story/new', methods=['POST'])
@login_required
def new_story():
    prompt = request.form['prompt']
    suggestion = generate_story_suggestion(prompt)
    story = Story(user_id=current_user.id, title=request.form['title'], content=suggestion)
    db.session.add(story)
    db.session.commit()
    socketio.emit('new_story', {'title': story.title, 'content': story.content})
    return redirect(url_for('storytelling.storytelling'))