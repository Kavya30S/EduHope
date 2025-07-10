from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models.social import Social
from app.models.user import User

social = Blueprint("social", __name__)

@social.route("/friends")
@login_required
def friends():
    friendships = Social.query.filter_by(user_id=current_user.id, status="accepted").all()
    friends = [User.query.get(f.friend_id) for f in friendships]
    return render_template("friends.html", friends=friends)

@social.route("/request", methods=["POST"])
@login_required
def send_request():
    friend_username = request.form["friend_username"]
    friend = User.query.filter_by(username=friend_username).first()
    if not friend:
        flash("User not found")
        return redirect(url_for("social.friends"))
    
    if Social.query.filter_by(user_id=current_user.id, friend_id=friend.id).first():
        flash("Request already sent")
    else:
        request = Social(user_id=current_user.id, friend_id=friend.id)
        db.session.add(request)
        db.session.commit()
        flash("Friend request sent!")
    return redirect(url_for("social.friends"))

@social.route("/accept/<int:request_id>")
@login_required
def accept_request(request_id):
    req = Social.query.get_or_404(request_id)
    if req.friend_id == current_user.id:
        req.accept()
        flash("Friend added!")
    return redirect(url_for("social.friends"))