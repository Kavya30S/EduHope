from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app.models.pet import Pet
from app import db, socketio

bp = Blueprint('pet_companion', __name__)

@bp.route('/pet', methods=['GET', 'POST'])
@login_required
def pet():
    pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not pet and request.method == 'POST':
        pet_type = request.form.get('pet_type', 'dragon')
        pet_name = request.form.get('pet_name', 'Buddy')
        pet = Pet(user_id=current_user.id, type=pet_type, name=pet_name)
        db.session.add(pet)
        db.session.commit()
        socketio.emit('pet_update', {
            'hunger': pet.hunger,
            'happiness': pet.happiness,
            'knowledge': pet.knowledge,
            'level': pet.level
        }, room=str(current_user.id))
    return render_template('pet.html', pet=pet)

@bp.route('/pet/feed', methods=['POST'])
@login_required
def feed_pet():
    pet = Pet.query.filter_by(user_id=current_user.id).first()
    if pet:
        pet.hunger = min(pet.hunger + 20, 100)
        pet.happiness = min(pet.happiness + 10, 100)
        if pet.hunger > 80:
            pet.happiness = min(pet.happiness + 5, 100)  # Bonus happiness for full tummy
        db.session.commit()
        socketio.emit('pet_update', {
            'hunger': pet.hunger,
            'happiness': pet.happiness
        }, room=str(current_user.id))
    return redirect(url_for('pet_companion.pet'))

@bp.route('/pet/play', methods=['POST'])
@login_required
def play_pet():
    pet = Pet.query.filter_by(user_id=current_user.id).first()
    if pet:
        pet.happiness = min(pet.happiness + 15, 100)
        pet.hunger = max(pet.hunger - 10, 0)
        pet.knowledge += 5  # Playing teaches tricks!
        if pet.knowledge >= pet.level * 100:
            pet.level += 1
            socketio.emit('level_up', {'level': pet.level}, room=str(current_user.id))
        db.session.commit()
        socketio.emit('pet_update', {
            'hunger': pet.hunger,
            'happiness': pet.happiness,
            'knowledge': pet.knowledge
        }, room=str(current_user.id))
    return redirect(url_for('pet_companion.pet'))