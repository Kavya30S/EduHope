from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models.user import User
from app.services.analytics_service import get_student_progress

teacher = Blueprint("teacher", __name__)

@teacher.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "teacher":
        flash("Access denied")
        return redirect(url_for("dashboard"))
    students = User.query.filter_by(role="student").all()
    return render_template("dashboard.html", students=students, teacher_view=True)

@teacher.route("/student/<int:student_id>")
@login_required
def student_progress(student_id):
    if current_user.role != "teacher":
        flash("Access denied")
        return redirect(url_for("dashboard"))
    student = User.query.get_or_404(student_id)
    progress, status = get_student_progress(student_id)
    if status != 200:
        flash(progress["error"])
        return redirect(url_for("teacher.dashboard"))
    return render_template("student_progress.html", student=student, progress=progress)