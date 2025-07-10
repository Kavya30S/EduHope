from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app.services.education_services import get_education_content, update_education_progress

education = Blueprint("education", __name__)

@education.route("/lessons")
@login_required
def lessons():
    content, status = get_education_content(current_user.id)
    if status != 200:
        flash(content["error"])
        return redirect(url_for("dashboard"))
    return render_template("lesson.html", lessons=content["lessons"], progress=content["game_progress"])

@education.route("/lesson/<int:lesson_id>", methods=["GET", "POST"])
@login_required
def lesson(lesson_id):
    if request.method == "POST":
        score = int(request.form["score"])
        time_spent = int(request.form.get("time_spent", 60))
        result, status = update_education_progress(current_user.id, lesson_id, score, time_spent)
        if status == 200:
            flash("Lesson completed!")
        else:
            flash(result["error"])
        return redirect(url_for("education.lessons"))

    lesson = Lesson.query.get_or_404(lesson_id)
    return render_template("lesson.html", lesson=lesson)