from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models.story import Story
from app.services.llm_service import generate_story_prompt

storytelling = Blueprint("storytelling", __name__)

@storytelling.route("/")
@login_required
def stories():
    user_stories = Story.query.filter_by(creator_id=current_user.id).all()
    return render_template("storytelling.html", stories=user_stories)

@storytelling.route("/create", methods=["GET", "POST"])
@login_required
def create_story():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        story = Story(title=title, content=content, creator_id=current_user.id)
        db.session.add(story)
        db.session.commit()
        flash("Story saved!")
        return redirect(url_for("storytelling.stories"))
    return render_template("create_story.html")

@storytelling.route("/generate", methods=["POST"])
@login_required
def generate_story():
    theme = request.form["theme"]
    result, status = generate_story_prompt(current_user.id, theme)
    if status == 200:
        return render_template("storytelling.html", generated_story=result["story"])
    flash(result["error"])
    return redirect(url_for("storytelling.stories"))