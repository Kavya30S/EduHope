from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('teacher', __name__)

@bp.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    lessons = Lesson.query.all()
    return render_template('dashboard.html', lessons=lessons, teacher_view=True)