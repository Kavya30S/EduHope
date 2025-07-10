from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app import db, cache
from app.models.lesson import Lesson
from app.services.adaptive_learning_services import get_personalized_lessons

education_bp = Blueprint('education', __name__)

@education_bp.route('/lessons')
@login_required
@cache.cached(timeout=60)
def lessons():
    lessons = get_personalized_lessons(current_user.id)
    return render_template('lesson.html', lessons=lessons)

@education_bp.route('/lesson/<int:id>')
@login_required
def view_lesson(id):
    lesson = Lesson.query.get_or_404(id)
    return render_template('lesson.html', lesson=lesson)