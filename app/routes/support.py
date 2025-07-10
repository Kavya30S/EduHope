from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app.services.support_services import get_support_messages, send_support_message

support = Blueprint("support", __name__)

@support.route("/")
@login_required
def support_page():
    messages, status = get_support_messages(current_user.id)
    if status != 200:
        flash(messages["error"])
        return redirect(url_for("dashboard"))
    return render_template("support.html", messages=messages)

@support.route("/send", methods=["POST"])
@login_required
def send_message():
    message = request.form["message"]
    result, status = send_support_message(current_user.id, message)
    if status == 200:
        flash("Message sent! Here’s our reply: " + result["response"])
    else:
        flash(result["error"])
    return redirect(url_for("support.support_page"))