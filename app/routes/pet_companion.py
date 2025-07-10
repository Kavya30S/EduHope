from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app.services.fantasy_pet_service import get_pet, update_pet_stats, customize_pet

pet_companion = Blueprint("pet_companion", __name__)

@pet_companion.route("/")
@login_required
def pet():
    pet_data, status = get_pet(current_user.id)
    if status != 200:
        flash(pet_data["error"])
        return redirect(url_for("dashboard"))
    return render_template("pet.html", pet=pet_data)

@pet_companion.route("/feed", methods=["POST"])
@login_required
def feed_pet():
    result, status = update_pet_stats(current_user.id, "feed")
    if status == 200:
        flash(result["message"])
    else:
        flash(result["error"])
    return redirect(url_for("pet_companion.pet"))

@pet_companion.route("/customize", methods=["POST"])
@login_required
def customize():
    accessory = request.form["accessory"]
    result, status = customize_pet(current_user.id, accessory)
    if status == 200:
        flash(result["message"])
    else:
        flash(result["error"])
    return redirect(url_for("pet_companion.pet"))