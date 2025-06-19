from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.pet import Pet
from app.models.user import User
from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement
from app.models.pet_item import PetItem
from app.models.user_pet_item import UserPetItem
from app import db
from datetime import datetime, timedelta
import random

pet = Blueprint('pet', __name__)

@pet.route('/')
@login_required
def index():
    """Main pet interface"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    
    if not user_pet:
        # Create a default pet if none exists
        user_pet = Pet(
            user_id=current_user.id,
            name=f"{current_user.username}'s Dragon",
            pet_type='dragon',
            level=1,
            experience=0,
            happiness=80,
            hunger=70,
            health=100,
            energy=90
        )
        db.session.add(user_pet)
        db.session.commit()
    
    # Get available items for purchase
    available_items = PetItem.query.filter_by(available=True).all()
    
    # Get user's items
    user_items = db.session.query(PetItem, UserPetItem).join(
        UserPetItem, PetItem.id == UserPetItem.item_id
    ).filter(UserPetItem.user_id == current_user.id).all()
    
    # Check if pet needs attention
    needs_attention = user_pet.hunger < 30 or user_pet.happiness < 40 or user_pet.energy < 20
    
    return render_template('pet/index.html', 
                         pet=user_pet, 
                         available_items=available_items,
                         user_items=user_items,
                         needs_attention=needs_attention)

@pet.route('/feed', methods=['POST'])
@login_required
def feed():
    """Feed the pet"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not user_pet:
        return jsonify({'success': False, 'message': 'Pet not found'})
    
    food_type = request.json.get('food_type', 'basic')
    food_costs = {'basic': 5, 'premium': 15, 'deluxe': 25}
    food_effects = {'basic': 20, 'premium': 40, 'deluxe': 60}
    
    cost = food_costs.get(food_type, 5)
    effect = food_effects.get(food_type, 20)
    
    if current_user.total_points < cost:
        return jsonify({'success': False, 'message': 'Not enough points!'})
    
    # Deduct points and feed pet
    current_user.total_points -= cost
    user_pet.hunger = min(100, user_pet.hunger + effect)
    user_pet.happiness = min(100, user_pet.happiness + 5)
    user_pet.last_fed = datetime.utcnow()
    user_pet.times_fed = (user_pet.times_fed or 0) + 1
    
    # Add experience
    exp_gain = effect // 4
    user_pet.experience += exp_gain
    
    # Check for level up
    level_up = False
    while user_pet.experience >= user_pet.level * 100:
        user_pet.experience -= user_pet.level * 100
        user_pet.level += 1
        level_up = True
        user_pet.max_happiness = min(100, user_pet.max_happiness + 5)
        user_pet.max_health = min(100, user_pet.max_health + 5)
    
    db.session.commit()
    
    # Check for feeding achievements
    check_feeding_achievements(user_pet.times_fed)
    
    response = {
        'success': True,
        'message': f'Fed {user_pet.name} with {food_type} food!',
        'pet': {
            'hunger': user_pet.hunger,
            'happiness': user_pet.happiness,
            'level': user_pet.level,
            'experience': user_pet.experience
        },
        'user_points': current_user.total_points,
        'level_up': level_up
    }
    
    if level_up:
        response['level_up_message'] = f'{user_pet.name} leveled up to level {user_pet.level}!'
    
    return jsonify(response)

@pet.route('/play', methods=['POST'])
@login_required
def play():
    """Play with the pet"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not user_pet:
        return jsonify({'success': False, 'message': 'Pet not found'})
    
    activity = request.json.get('activity', 'fetch')
    
    if user_pet.energy < 20:
        return jsonify({'success': False, 'message': f'{user_pet.name} is too tired to play!'})
    
    # Different activities have different effects
    activities = {
        'fetch': {'happiness': 25, 'energy': -15, 'experience': 10},
        'tricks': {'happiness': 30, 'energy': -20, 'experience': 15},
        'cuddle': {'happiness': 20, 'energy': -5, 'experience': 5},
        'training': {'happiness': 15, 'energy': -25, 'experience': 25}
    }
    
    effects = activities.get(activity, activities['fetch'])
    
    # Apply effects
    user_pet.happiness = min(user_pet.max_happiness, user_pet.happiness + effects['happiness'])
    user_pet.energy = max(0, user_pet.energy + effects['energy'])
    user_pet.experience += effects['experience']
    user_pet.last_played = datetime.utcnow()
    user_pet.times_played = (user_pet.times_played or 0) + 1
    
    # Check for level up
    level_up = False
    while user_pet.experience >= user_pet.level * 100:
        user_pet.experience -= user_pet.level * 100
        user_pet.level += 1
        level_up = True
    
    db.session.commit()
    
    # Generate random positive message
    messages = [
        f'{user_pet.name} loved playing {activity}!',
        f'{user_pet.name} is so happy after {activity}!',
        f'Great {activity} session with {user_pet.name}!',
        f'{user_pet.name} wants to play {activity} again!'
    ]
    
    return jsonify({
        'success': True,
        'message': random.choice(messages),
        'pet': {
            'happiness': user_pet.happiness,
            'energy': user_pet.energy,
            'level': user_pet.level,
            'experience': user_pet.experience
        },
        'level_up': level_up
    })

@pet.route('/heal', methods=['POST'])
@login_required
def heal():
    """Heal the pet"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not user_pet:
        return jsonify({'success': False, 'message': 'Pet not found'})
    
    heal_cost = 10
    if current_user.total_points < heal_cost:
        return jsonify({'success': False, 'message': 'Not enough points!'})
    
    if user_pet.health >= user_pet.max_health:
        return jsonify({'success': False, 'message': f'{user_pet.name} is already healthy!'})
    
    current_user.total_points -= heal_cost
    user_pet.health = user_pet.max_health
    user_pet.happiness = min(user_pet.max_happiness, user_pet.happiness + 10)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{user_pet.name} is now fully healed!',
        'pet': {
            'health': user_pet.health,
            'happiness': user_pet.happiness
        },
        'user_points': current_user.total_points
    })

@pet.route('/rest', methods=['POST'])
@login_required
def rest():
    """Let the pet rest to restore energy"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not user_pet:
        return jsonify({'success': False, 'message': 'Pet not found'})
    
    if user_pet.energy >= 100:
        return jsonify({'success': False, 'message': f'{user_pet.name} is already full of energy!'})
    
    # Check if enough time has passed since last rest
    if user_pet.last_rested and (datetime.utcnow() - user_pet.last_rested).seconds < 300:  # 5 minutes
        return jsonify({'success': False, 'message': f'{user_pet.name} needs more time to rest!'})
    
    user_pet.energy = min(100, user_pet.energy + 30)
    user_pet.last_rested = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{user_pet.name} feels refreshed after resting!',
        'pet': {
            'energy': user_pet.energy
        }
    })

@pet.route('/rename', methods=['POST'])
@login_required
def rename():
    """Rename the pet"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not user_pet:
        return jsonify({'success': False, 'message': 'Pet not found'})
    
    new_name = request.json.get('name', '').strip()
    
    if not new_name or len(new_name) < 2:
        return jsonify({'success': False, 'message': 'Name must be at least 2 characters long'})
    
    if len(new_name) > 20:
        return jsonify({'success': False, 'message': 'Name must be less than 20 characters'})
    
    old_name = user_pet.name
    user_pet.name = new_name
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Pet renamed from {old_name} to {new_name}!',
        'pet': {
            'name': user_pet.name
        }
    })

@pet.route('/shop')
@login_required
def shop():
    """Pet shop for buying items"""
    available_items = PetItem.query.filter_by(available=True).all()
    user_items = db.session.query(PetItem, UserPetItem).join(
        UserPetItem, PetItem.id == UserPetItem.item_id
    ).filter(UserPetItem.user_id == current_user.id).all()
    
    user_item_ids = {item[1].item_id for item in user_items}
    
    return render_template('pet/shop.html', 
                         available_items=available_items,
                         user_item_ids=user_item_ids,
                         user_points=current_user.total_points)

@pet.route('/buy_item', methods=['POST'])
@login_required
def buy_item():
    """Buy an item for the pet"""
    item_id = request.json.get('item_id')
    item = PetItem.query.get(item_id)
    
    if not item or not item.available:
        return jsonify({'success': False, 'message': 'Item not found'})
    
    # Check if user already owns this item
    existing = UserPetItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if existing:
        return jsonify({'success': False, 'message': 'You already own this item'})
    
    if current_user.total_points < item.cost:
        return jsonify({'success': False, 'message': 'Not enough points!'})
    
    # Purchase item
    current_user.total_points -= item.cost
    user_item = UserPetItem(user_id=current_user.id, item_id=item_id)
    db.session.add(user_item)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Successfully bought {item.name}!',
        'user_points': current_user.total_points
    })

@pet.route('/use_item', methods=['POST'])
@login_required
def use_item():
    """Use an item on the pet"""
    item_id = request.json.get('item_id')
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    
    if not user_pet:
        return jsonify({'success': False, 'message': 'Pet not found'})
    
    # Check if user owns the item
    user_item = UserPetItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if not user_item:
        return jsonify({'success': False, 'message': 'You do not own this item'})
    
    item = PetItem.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'message': 'Item not found'})
    
    # Apply item effects
    effects_applied = []
    
    if item.happiness_effect:
        user_pet.happiness = min(user_pet.max_happiness, user_pet.happiness + item.happiness_effect)
        effects_applied.append(f'Happiness +{item.happiness_effect}')
    
    if item.health_effect:
        user_pet.health = min(user_pet.max_health, user_pet.health + item.health_effect)
        effects_applied.append(f'Health +{item.health_effect}')
    
    if item.energy_effect:
        user_pet.energy = min(100, user_pet.energy + item.energy_effect)
        effects_applied.append(f'Energy +{item.energy_effect}')
    
    if item.hunger_effect:
        user_pet.hunger = min(100, user_pet.hunger + item.hunger_effect)
        effects_applied.append(f'Hunger +{item.hunger_effect}')
    
    # Use up the item if it's consumable
    if item.consumable:
        db.session.delete(user_item)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Used {item.name} on {user_pet.name}! ' + ', '.join(effects_applied),
        'pet': {
            'happiness': user_pet.happiness,
            'health': user_pet.health,
            'energy': user_pet.energy,
            'hunger': user_pet.hunger
        }
    })

@pet.route('/playground')
@login_required
def playground():
    """Virtual playground where pets can interact"""
    # Get all pets that are currently "online" (active in last hour)
    online_pets = db.session.query(Pet, User).join(User, Pet.user_id == User.id).filter(
        User.last_seen >= datetime.utcnow() - timedelta(hours=1)
    ).limit(20).all()
    
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    
    return render_template('pet/playground.html', 
                         online_pets=online_pets,
                         user_pet=user_pet)

@pet.route('/stats')
@login_required
def stats():
    """Detailed pet statistics"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not user_pet:
        return redirect(url_for('pet.index'))
    
    # Calculate various stats
    stats = {
        'age_days': (datetime.utcnow() - user_pet.created_at).days,
        'times_fed': user_pet.times_fed or 0,
        'times_played': user_pet.times_played or 0,
        'level_progress': (user_pet.experience / (user_pet.level * 100)) * 100,
        'happiness_level': get_happiness_level(user_pet.happiness),
        'health_status': get_health_status(user_pet.health),
        'energy_level': get_energy_level(user_pet.energy)
    }
    
    return render_template('pet/stats.html', pet=user_pet, stats=stats)

def check_feeding_achievements(times_fed):
    """Check and award feeding-related achievements"""
    if times_fed == 10:
        award_achievement(current_user.id, 'Pet Caretaker')

def award_achievement(user_id, achievement_name):
    """Award an achievement to a user"""
    achievement = Achievement.query.filter_by(name=achievement_name).first()
    if not achievement:
        return
    
    # Check if user already has this achievement
    existing = UserAchievement.query.filter_by(
        user_id=user_id, 
        achievement_id=achievement.id
    ).first()
    
    if not existing:
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement.id
        )
        db.session.add(user_achievement)
        
        # Add points to user
        user = User.query.get(user_id)
        user.total_points += achievement.points
        db.session.commit()

def get_happiness_level(happiness):
    """Convert happiness number to descriptive level"""
    if happiness >= 80:
        return "Ecstatic"
    elif happiness >= 60:
        return "Happy"
    elif happiness >= 40:
        return "Content"
    elif happiness >= 20:
        return "Sad"
    else:
        return "Depressed"

def get_health_status(health):
    """Convert health number to descriptive status"""
    if health >= 80:
        return "Excellent"
    elif health >= 60:
        return "Good"
    elif health >= 40:
        return "Fair"
    elif health >= 20:
        return "Poor"
    else:
        return "Critical"

def get_energy_level(energy):
    """Convert energy number to descriptive level"""
    if energy >= 80:
        return "Energetic"
    elif energy >= 60:
        return "Active"
    elif energy >= 40:
        return "Moderate"
    elif energy >= 20:
        return "Tired"
    else:
        return "Exhausted"

@pet.route('/api/status')
@login_required
def api_status():
    """API endpoint for getting pet status"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not user_pet:
        return jsonify({'error': 'Pet not found'}), 404
    
    return jsonify({
        'name': user_pet.name,
        'type': user_pet.pet_type,
        'level': user_pet.level,
        'experience': user_pet.experience,
        'happiness': user_pet.happiness,
        'hunger': user_pet.hunger,
        'health': user_pet.health,
        'energy': user_pet.energy,
        'needs_attention': user_pet.hunger < 30 or user_pet.happiness < 40 or user_pet.energy < 20
    })