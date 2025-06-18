from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.services.llm_service import LLMService

bp = Blueprint('education', __name__)
llm_service = LLMService()

@bp.route('/dashboard')
@login_required
def dashboard():
    lessons = Lesson.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', lessons=lessons)

@bp.route('/generate_lesson')
@login_required
def generate_lesson():
    prompt = "Generate a simple lesson about animals for children."
    content = llm_service.generate_lesson(prompt)
    lesson = Lesson(title="Animal Lesson", content=content, user_id=current_user.id)
    db.session.add(lesson)
    db.session.commit()
    return redirect(url_for('education.dashboard'))