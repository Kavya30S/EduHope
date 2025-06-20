from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
from app.models.pet import Pet
from app.models.user import User
from app import db
import json
from datetime import datetime, timedelta
import random

pet_bp = Blueprint('pet', __name__)

@pet_bp.route('/pet')
@login_required
def pet_dashboard():
    """Main pet dashboard"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    
    if not user_pet:
        # Redirect to pet selection if no pet exists
        return redirect(url_for('pet.select_pet'))
    
    # Check if pet needs automatic stat updates (time-based decay)
    update_pet_time_based_stats(user_pet)
    
    available_pets = Pet.get_available_pets()
    unlocked_pets = [pet for pet in available_pets if pet['unlock_requirement'] <= current_user.total_score]
    
    return render_template('pet.html', 
                         pet=user_pet, 
                         pet_status=user_pet.get_status(),
                         unlocked_pets=unlocked_pets,
                         available_accessories=get_available_accessories(user_pet.level),
                         available_toys=get_available_toys(user_pet.level))

@pet_bp.route('/select-pet')
@login_required
def select_pet():
    """Pet selection page for new users"""
    existing_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if existing_pet:
        return redirect(url_for('pet.pet_dashboard'))
    
    available_pets = Pet.get_available_pets()
    unlocked_pets = [pet for pet in available_pets if pet['unlock_requirement'] <= current_user.total_score]
    
    return render_template('pet_selection.html', pets=unlocked_pets)

@pet_bp.route('/create-pet', methods=['POST'])
@login_required
def create_pet():
    """Create a new pet for the user"""
    data = request.get_json()
    
    # Check if user already has a pet
    existing_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if existing_pet:
        return jsonify({'error': 'You already have a pet!'}), 400
    
    pet_type = data.get('pet_type')
    pet_name = data.get('pet_name', '').strip()
    
    if not pet_name:
        return jsonify({'error': 'Pet name is required!'}), 400
    
    if len(pet_name) > 20:
        return jsonify({'error': 'Pet name must be 20 characters or less!'}), 400
    
    # Validate pet type
    available_pets = Pet.get_available_pets()
    valid_pet = next((pet for pet in available_pets if pet['type'] == pet_type), None)
    
    if not valid_pet:
        return jsonify({'error': 'Invalid pet type!'}), 400
    
    # Check if pet is unlocked
    if valid_pet['unlock_requirement'] > current_user.total_score:
        return jsonify({'error': 'Pet not yet unlocked!'}), 400
    
    # Create new pet
    new_pet = Pet(
        user_id=current_user.id,
        name=pet_name,
        pet_type=pet_type,
        personality_traits=json.dumps(valid_pet['personality'])
    )
    
    db.session.add(new_pet)
    db.session.commit()
    
    # Add initial accessories for starter pets
    if valid_pet['unlock_requirement'] == 0:
        new_pet.add_accessory('Basic Collar')
        new_pet.add_toy('Starter Ball')
        db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Welcome {pet_name}! Your new companion is ready!',
        'pet': new_pet.to_dict()
    })

@pet_bp.route('/feed', methods=['POST'])
@login_required
def feed_pet():
    """Feed the pet"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not user_pet:
        return jsonify({'error': 'No pet found!'}), 404
    
    data = request.get_json()
    food_type = data.get('food_type', 'regular')
    
    # Check if user has enough points for premium food
    food_costs = {
        'regular': 0,
        'premium': 10,
        'magical': 25
    }
    
    cost = food_costs.get(food_type, 0)
    if cost > current_user.points:
        return jsonify({'error': 'Not enough points for this food!'}), 400
    
    # Check feeding cooldown (can't feed too frequently)
    if user_pet.last_fed:
        time_since_feed = datetime.utcnow() - user_pet.last_fed
        if time_since_feed < timedelta(minutes=30):
            remaining_time = 30 - int(time_since_feed.total_seconds() / 60)
            return jsonify({'error': f'Pet is not hungry yet! Wait {remaining_time} more minutes.'}), 400
    
    # Deduct points and feed pet
    current_user.points -= cost
    user_pet.feed(food_type)
    
    db.session.commit()
    
    # Generate feeding message
    feeding_messages = {
        'regular': [
            f"{user_pet.name} happily munches on the food!",
            f"{user_pet.name} enjoys the tasty meal!",
            f"{user_pet.name} gobbles up the food with joy!"
        ],
        'premium': [
            f"{user_pet.name} is delighted with the premium feast!",
            f"{user_pet.name} savors every bite of the delicious meal!",
            f"{user_pet.name} feels very special with this premium food!"
        ],
        'magical': [
            f"{user_pet.name} glows with magical energy after eating!",
            f"{user_pet.name} feels the magic coursing through their body!",
            f"{user_pet.name} sparkles with newfound magical power!"
        ]
    }
    
    message = random.choice(feeding_messages[food_type])
    
    return jsonify({
        'success': True,
        'message': message,
        'pet_status': user_pet.get_status(),
        'user_points': current_user.points
    })

@pet_bp.route('/play', methods=['POST'])
@login_required
def play_with_pet():
    """Play with the pet"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not user_pet:
        return jsonify({'error': 'No pet found!'}), 404
    
    data = request.get_json()
    activity = data.get('activity', 'basic')
    
    # Check if pet has enough energy
    if user_pet.energy < 10:
        return jsonify({'error': f'{user_pet.name} is too tired to play! Let them rest or feed them some magical food.'}), 400
    
    # Check play cooldown
    if user_pet.last_played:
        time_since_play = datetime.utcnow() - user_pet.last_played
        if time_since_play < timedelta(minutes=15):
            remaining_time = 15 - int(time_since_play.total_seconds() / 60)
            return jsonify({'error': f'{user_pet.name} needs to rest! Wait {remaining_time} more minutes.'}), 400
    
    # Play with pet
    success = user_pet.play(activity)
    
    if not success:
        return jsonify({'error': f'{user_pet.name} is too tired for this activity!'}), 400
    
    db.session.commit()
    
    # Generate play messages
    play_messages = {
        'basic': [
            f"{user_pet.name} has a wonderful time playing!",
            f"{user_pet.name} jumps around with excitement!",
            f"{user_pet.name} loves spending time with you!"
        ],
        'training': [
            f"{user_pet.name} learns new tricks during training!",
            f"{user_pet.name} becomes stronger and smarter!",
            f"{user_pet.name} enjoys the challenging training session!"
        ],
        'adventure': [
            f"{user_pet.name} discovers amazing things on the adventure!",
            f"{user_pet.name} feels brave and adventurous!",
            f"{user_pet.name} returns from adventure with glowing eyes!"
        ]
    }
    
    message = random.choice(play_messages[activity])
    
    # Check for level up
    level_up_message = ""
    if user_pet.experience >= user_pet.level * 100:
        level_up_message = f" 🎉 {user_pet.name} leveled up to Level {user_pet.level}! New rewards unlocked!"
    
    return jsonify({
        'success': True,
        'message': message + level_up_message,
        'pet_status': user_pet.get_status(),
        'level_up': level_up_message != ""
    })

@pet_bp.route('/care', methods=['POST'])
@login_required
def care_for_pet():
    """General care activities (grooming, healing, etc.)"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not user_pet:
        return jsonify({'error': 'No pet found!'}), 404
    
    data = request.get_json()
    care_type = data.get('care_type', 'groom')
    
    care_effects = {
        'groom': {
            'happiness': 15,
            'health': 10,
            'cost': 5,
            'messages': [
                f"{user_pet.name} looks beautiful after grooming!",
                f"{user_pet.name} sparkles with cleanliness!",
                f"{user_pet.name} feels fresh and happy!"
            ]
        },
        'heal': {
            'health': 30,
            'happiness': 5,
            'cost': 15,
            'messages': [
                f"{user_pet.name} feels much better now!",
                f"{user_pet.name} is fully healed and healthy!",
                f"{user_pet.name} bounces back with renewed vigor!"
            ]
        },
        'massage': {
            'happiness': 20,
            'energy': 15,
            'cost': 10,
            'messages': [
                f"{user_pet.name} purrs with contentment during the massage!",
                f"{user_pet.name} feels so relaxed and happy!",
                f"{user_pet.name} enjoys the soothing massage!"
            ]
        }
    }
    
    if care_type not in care_effects:
        return jsonify({'error': 'Invalid care type!'}), 400
    
    care = care_effects[care_type]
    
    # Check if user has enough points
    if care['cost'] > current_user.points:
        return jsonify({'error': 'Not enough points for this care activity!'}), 400
    
    # Apply care effects
    current_user.points -= care['cost']
    
    if 'happiness' in care:
        user_pet.happiness = min(100, user_pet.happiness + care['happiness'])
    if 'health' in care:
        user_pet.health = min(100, user_pet.health + care['health'])
    if 'energy' in care:
        user_pet.energy = min(100, user_pet.energy + care['energy'])
    
    user_pet.experience += 5  # Small experience gain for caring
    
    db.session.commit()
    
    message = random.choice(care['messages'])
    
    return jsonify({
        'success': True,
        'message': message,
        'pet_status': user_pet.get_status(),
        'user_points': current_user.points
    })

@pet_bp.route('/status')
@login_required
def get_pet_status():
    """Get current pet status"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not user_pet:
        return jsonify({'error': 'No pet found!'}), 404
    
    update_pet_time_based_stats(user_pet)
    
    return jsonify({
        'pet_status': user_pet.get_status(),
        'time_until_next_feed': get_time_until_next_feed(user_pet),
        'time_until_next_play': get_time_until_next_play(user_pet)
    })

@pet_bp.route('/pet-shop')
@login_required
def pet_shop():
    """Pet shop for accessories and toys"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not user_pet:
        return jsonify({'error': 'No pet found!'}), 404
    
    available_accessories = get_available_accessories(user_pet.level)
    available_toys = get_available_toys(user_pet.level)
    
    return jsonify({
        'accessories': available_accessories,
        'toys': available_toys,
        'user_points': current_user.points,
        'pet_level': user_pet.level
    })

@pet_bp.route('/buy-item', methods=['POST'])
@login_required
def buy_item():
    """Buy accessory or toy for pet"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not user_pet:
        return jsonify({'error': 'No pet found!'}), 404
    
    data = request.get_json()
    item_type = data.get('item_type')  # 'accessory' or 'toy'
    item_name = data.get('item_name')
    
    # Get item details
    if item_type == 'accessory':
        available_items = get_available_accessories(user_pet.level)
    elif item_type == 'toy':
        available_items = get_available_toys(user_pet.level)
    else:
        return jsonify({'error': 'Invalid item type!'}), 400
    
    item = next((item for item in available_items if item['name'] == item_name), None)
    if not item:
        return jsonify({'error': 'Item not found!'}), 404
    
    # Check if already owned
    if item_type == 'accessory' and item_name in user_pet.get_unlocked_accessories():
        return jsonify({'error': 'You already own this accessory!'}), 400
    if item_type == 'toy' and item_name in user_pet.get_unlocked_toys():
        return jsonify({'error': 'You already own this toy!'}), 400
    
    # Check if user has enough points
    if item['cost'] > current_user.points:
        return jsonify({'error': 'Not enough points!'}), 400
    
    # Purchase item
    current_user.points -= item['cost']
    
    if item_type == 'accessory':
        user_pet.add_accessory(item_name)
    else:
        user_pet.add_toy(item_name)
    
    # Add experience for purchasing
    user_pet.experience += 10
    user_pet.happiness = min(100, user_pet.happiness + 15)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{user_pet.name} loves their new {item_name}!',
        'pet_status': user_pet.get_status(),
        'user_points': current_user.points
    })

def update_pet_time_based_stats(pet):
    """Update pet stats based on time passed"""
    now = datetime.utcnow()
    
    # Hunger increases over time
    if pet.last_fed:
        hours_since_feed = (now - pet.last_fed).total_seconds() / 3600
        hunger_increase = int(hours_since_feed * 5)  # 5 hunger per hour
        pet.hunger = min(100, pet.hunger + hunger_increase)
    
    # Energy regenerates over time if well-fed
    if pet.hunger < 70:
        hours_since_last_update = (now - pet.created_at).total_seconds() / 3600
        energy_regen = int(hours_since_last_update * 2)  # 2 energy per hour
        pet.energy = min(100, pet.energy + energy_regen)
    
    # Happiness decreases if neglected
    if pet.last_played:
        hours_since_play = (now - pet.last_played).total_seconds() / 3600
        if hours_since_play > 24:  # If not played with for over 24 hours
            happiness_decrease = int((hours_since_play - 24) * 2)
            pet.happiness = max(0, pet.happiness - happiness_decrease)

def get_time_until_next_feed(pet):
    """Get time until pet can be fed again"""
    if not pet.last_fed:
        return 0
    
    time_since_feed = datetime.utcnow() - pet.last_fed
    cooldown_minutes = 30
    remaining_minutes = cooldown_minutes - int(time_since_feed.total_seconds() / 60)
    
    return max(0, remaining_minutes)

def get_time_until_next_play(pet):
    """Get time until pet can play again"""
    if not pet.last_played:
        return 0
    
    time_since_play = datetime.utcnow() - pet.last_played
    cooldown_minutes = 15
    remaining_minutes = cooldown_minutes - int(time_since_play.total_seconds() / 60)
    
    return max(0, remaining_minutes)

def get_available_accessories(pet_level):
    """Get accessories available for purchase based on pet level"""
    accessories = [
        {'name': 'Sparkly Collar', 'cost': 20, 'level_requirement': 1, 'description': 'A beautiful collar that sparkles in the light!'},
        {'name': 'Magic Hat', 'cost': 35, 'level_requirement': 3, 'description': 'A hat that makes your pet look wise and magical!'},
        {'name': 'Wings of Wonder', 'cost': 50, 'level_requirement': 5, 'description': 'Magnificent wings that let your pet soar!'},
        {'name': 'Crown of Wisdom', 'cost': 75, 'level_requirement': 7, 'description': 'A golden crown for the smartest pets!'},
        {'name': 'Armor of Courage', 'cost': 100, 'level_requirement': 10, 'description': 'Protective armor for brave adventures!'},
        {'name': 'Cape of Heroes', 'cost': 150, 'level_requirement': 15, 'description': 'A heroic cape that flows in the wind!'},
        {'name': 'Legendary Aura', 'cost': 200, 'level_requirement': 20, 'description': 'A mystical aura that surrounds legendary pets!'}
    ]
    
    return [acc for acc in accessories if acc['level_requirement'] <= pet_level]

def get_available_toys(pet_level):
    """Get toys available for purchase based on pet level"""
    toys = [
        {'name': 'Rainbow Ball', 'cost': 15, 'level_requirement': 1, 'description': 'A bouncy ball that changes colors!'},
        {'name': 'Glowing Stick', 'cost': 25, 'level_requirement': 2, 'description': 'A stick that glows with magical light!'},
        {'name': 'Puzzle Cube', 'cost': 40, 'level_requirement': 4, 'description': 'A challenging puzzle that boosts intelligence!'},
        {'name': 'Melody Box', 'cost': 60, 'level_requirement': 6, 'description': 'A music box that plays beautiful tunes!'},
        {'name': 'Time Crystal', 'cost': 85, 'level_requirement': 8, 'description': 'A crystal that shows glimpses of the future!'},
        {'name': 'Dream Catcher', 'cost': 120, 'level_requirement': 12, 'description': 'Catches nightmares and brings sweet dreams!'},
        {'name': 'Infinity Stone', 'cost': 180, 'level_requirement': 18, 'description': 'A powerful stone with infinite possibilities!'}
    ]
    
    return [toy for toy in toys if toy['level_requirement'] <= pet_level]