from flask import current_app
from app.models.pet import Pet
from app.models.user import User
import json

def get_pet_behavior(user_id):
    """
    Retrieve pet's current behavior based on stats.
    """
    pet = Pet.query.filter_by(user_id=user_id).first()
    if not pet:
        return {"error": "Pet not found"}, 404

    mood = pet.get_mood()
    behaviors = {
        "Super Happy": "dancing around with joy",
        "Happy": "wagging its tail happily",
        "Okay": "looking curious",
        "Sad": "sitting quietly",
        "Very Sad": "hiding under a blanket"
    }
    behavior = behaviors.get(mood["mood"], "playing gently")
    return {"behavior": behavior, "mood": mood}, 200

def update_pet_behavior(user_id, action):
    """
    Update pet behavior based on user interaction.
    """
    pet = Pet.query.filter_by(user_id=user_id).first()
    if not pet:
        return {"error": "Pet not found"}, 404

    if action == "talk":
        pet.happiness = min(100, pet.happiness + 10)
        message = f"🐾 {pet.name} loves hearing your voice!"
    elif action == "pat":
        pet.happiness = min(100, pet.happiness + 15)
        message = f"💖 {pet.name} purrs happily!"
    else:
        return {"error": "Invalid action"}, 400

    db.session.commit()
    return {"pet": pet.to_dict(), "message": message}, 200

def get_pet_interactions(user_id):
    """
    Retrieve recent pet interactions.
    """
    pet = Pet.query.filter_by(user_id=user_id).first()
    if not pet:
        return {"error": "Pet not found"}, 404

    interactions = [
        {"action": "fed", "timestamp": pet.last_fed.isoformat(), "effect": "Yummy meal!"},
        {"action": "played", "timestamp": pet.last_played.isoformat(), "effect": "Fun time!"}
    ]
    return {"interactions": interactions, "current_mood": pet.get_mood()}, 200