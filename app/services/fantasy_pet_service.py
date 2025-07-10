from flask import current_app
from app.models.pet import Pet
from app.models.user import User
from app.models.achievement import Achievement, UserAchievement
import json

def get_pet(user_id):
    """
    Retrieve user's fantasy pet details.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    pet = Pet.query.filter_by(user_id=user_id).first()
    if not pet:
        pet = Pet(user_id=user_id, name=f"{user.username}'s Pet", pet_type="dragon")
        db.session.add(pet)
        db.session.commit()

    return pet.to_dict(), 200

def update_pet_stats(user_id, action):
    """
    Update pet stats based on user actions.
    """
    pet = Pet.query.filter_by(user_id=user_id).first()
    if not pet:
        return {"error": "Pet not found"}, 404

    if action == "feed":
        result = pet.feed()
    elif action == "play":
        result = pet.play()
    elif action == "rest":
        pet.energy = min(100, pet.energy + 20)
        pet.happiness = min(100, pet.happiness + 5)
        result = f"💤 {pet.name} feels refreshed!"
    else:
        return {"error": "Invalid action"}, 400

    db.session.commit()
    check_pet_achievements(user_id, pet)
    return {"pet": pet.to_dict(), "message": result}, 200

def customize_pet(user_id, accessory):
    """
    Customize pet with an accessory.
    """
    pet = Pet.query.filter_by(user_id=user_id).first()
    if not pet:
        return {"error": "Pet not found"}, 404

    pet.add_accessory(accessory)
    pet.happiness = min(100, pet.happiness + 10)
    db.session.commit()

    return {"pet": pet.to_dict(), "message": f"✨ {pet.name} loves the new {accessory}!"}, 200

def check_pet_achievements(user_id, pet):
    """
    Check for pet-related achievements.
    """
    achievements = Achievement.query.filter_by(category="pet_care").all()
    for ach in achievements:
        if ach.check_requirements(pet.get_mood()) and not UserAchievement.query.filter_by(user_id=user_id, achievement_id=ach.id).first():
            user_ach = UserAchievement(user_id=user_id, achievement_id=ach.id)
            db.session.add(user_ach)
            db.session.commit()