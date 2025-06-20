from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models.user import User, db
from app.models.pet import Pet
from app.services.sentiment_service import analyze_emotion
import random

auth_bp = Blueprint('auth', __name__)

# Fantasy pet choices with unique attributes
FANTASY_PETS = {
    'dragon': {'name': 'Flame Guardian', 'type': 'fire', 'special': 'wisdom_boost', 'rarity': 'legendary'},
    'unicorn': {'name': 'Starlight Healer', 'type': 'magic', 'special': 'health_restore', 'rarity': 'mythical'},
    'phoenix': {'name': 'Ember Phoenix', 'type': 'fire', 'special': 'rebirth_power', 'rarity': 'legendary'},
    'griffin': {'name': 'Sky Protector', 'type': 'air', 'special': 'flight_speed', 'rarity': 'rare'},
    'pegasus': {'name': 'Cloud Dancer', 'type': 'air', 'special': 'dream_flight', 'rarity': 'rare'},
    'fairy_cat': {'name': 'Sparkle Whiskers', 'type': 'magic', 'special': 'luck_charm', 'rarity': 'uncommon'},
    'crystal_wolf': {'name': 'Frost Howler', 'type': 'ice', 'special': 'ice_shield', 'rarity': 'rare'},
    'rainbow_fox': {'name': 'Prism Tail', 'type': 'magic', 'special': 'color_magic', 'rarity': 'uncommon'},
    'star_bear': {'name': 'Cosmic Cuddles', 'type': 'space', 'special': 'star_power', 'rarity': 'rare'},
    'moon_rabbit': {'name': 'Luna Hopper', 'type': 'space', 'special': 'moon_jump', 'rarity': 'uncommon'},
    'sea_dragon': {'name': 'Coral Guardian', 'type': 'water', 'special': 'water_breath', 'rarity': 'legendary'},
    'forest_sprite': {'name': 'Leaf Dancer', 'type': 'nature', 'special': 'plant_growth', 'rarity': 'uncommon'},
    'storm_eagle': {'name': 'Thunder Wing', 'type': 'storm', 'special': 'lightning_speed', 'rarity': 'rare'},
    'shadow_panther': {'name': 'Night Stalker', 'type': 'shadow', 'special': 'stealth_mode', 'rarity': 'rare'},
    'light_deer': {'name': 'Golden Antler', 'type': 'light', 'special': 'healing_light', 'rarity': 'rare'},
    'earth_turtle': {'name': 'Rocky Shield', 'type': 'earth', 'special': 'earth_armor', 'rarity': 'uncommon'},
    'wind_serpent': {'name': 'Zephyr Coil', 'type': 'air', 'special': 'wind_dance', 'rarity': 'rare'},
    'fire_salamander': {'name': 'Magma Crawler', 'type': 'fire', 'special': 'lava_walk', 'rarity': 'uncommon'},
    'ice_phoenix': {'name': 'Frost Feather', 'type': 'ice', 'special': 'freeze_time', 'rarity': 'legendary'},
    'dream_butterfly': {'name': 'Mystic Wings', 'type': 'dream', 'special': 'dream_weaving', 'rarity': 'mythical'},
    'cosmic_owl': {'name': 'Nebula Eyes', 'type': 'space', 'special': 'cosmic_sight', 'rarity': 'rare'},
    'crystal_dragon': {'name': 'Gem Scale', 'type': 'crystal', 'special': 'crystal_power', 'rarity': 'legendary'},
    'spirit_wolf': {'name': 'Ghost Howl', 'type': 'spirit', 'special': 'phase_walk', 'rarity': 'rare'},
    'flower_fairy': {'name': 'Petal Dance', 'type': 'nature', 'special': 'bloom_magic', 'rarity': 'uncommon'}
}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            
            # Check if user needs to complete assessment or choose pet
            if not user.assessment_completed:
                return jsonify({'redirect': '/assessment'}) if request.is_json else redirect(url_for('assessment.start'))
            elif not user.pet_id:
                return jsonify({'redirect': '/choose-pet'}) if request.is_json else redirect(url_for('auth.choose_pet'))
            else:
                # Update user's last login and mood
                if 'mood_score' in data:
                    emotion_result = analyze_emotion(data.get('mood_text', ''))
                    user.current_mood = emotion_result['emotion']
                    user.mood_score = emotion_result['confidence']
                
                user.login_streak += 1
                user.total_logins += 1
                db.session.commit()
                
                return jsonify({'redirect': '/dashboard'}) if request.is_json else redirect(url_for('main.dashboard'))
        else:
            message = 'Invalid username or password! Try again, little explorer! 🌟'
            if request.is_json:
                return jsonify({'error': message}), 401
            flash(message)
    
    return render_template('login.html', pets=FANTASY_PETS)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        age = int(data.get('age', 8))
        preferred_language = data.get('language', 'en')
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            message = 'Username already exists! Choose a unique magical name! ✨'
            if request.is_json:
                return jsonify({'error': message}), 400
            flash(message)
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            age=age,
            preferred_language=preferred_language,
            learning_level=max(1, min(age - 5, 5)),  # Age-appropriate level
            experience_points=0,
            learning_streak=0,
            total_lessons_completed=0,
            assessment_completed=False
        )
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return jsonify({'redirect': '/assessment'}) if request.is_json else redirect(url_for('assessment.start'))
    
    return render_template('register.html')

@auth_bp.route('/choose-pet')
@login_required
def choose_pet():
    if current_user.pet_id:
        return redirect(url_for('main.dashboard'))
    
    # Randomize pet order for variety
    pets_list = list(FANTASY_PETS.items())
    random.shuffle(pets_list)
    
    return render_template('choose_pet.html', 
                         pets=dict(pets_list),
                         user_level=current_user.learning_level)

@auth_bp.route('/select-pet', methods=['POST'])
@login_required
def select_pet():
    data = request.get_json() if request.is_json else request.form
    pet_type = data.get('pet_type')
    pet_name = data.get('pet_name', FANTASY_PETS.get(pet_type, {}).get('name', 'My Pet'))
    
    if pet_type not in FANTASY_PETS:
        return jsonify({'error': 'Invalid pet selection!'}), 400
    
    # Create new pet for user
    pet_data = FANTASY_PETS[pet_type]
    pet = Pet(
        user_id=current_user.id,
        name=pet_name,
        pet_type=pet_type,
        species=pet_data['name'],
        element_type=pet_data['type'],
        special_ability=pet_data['special'],
        rarity=pet_data['rarity'],
        level=1,
        experience=0,
        happiness=80,  # Start happy
        hunger=20,     # Start not too hungry
        health=100,    # Perfect health
        energy=100,    # Full energy
        accessories_unlocked=[],
        last_fed=db.func.now(),
        last_played=db.func.now()
    )
    
    db.session.add(pet)
    db.session.flush()  # Get pet ID
    
    # Link pet to user
    current_user.pet_id = pet.id
    current_user.total_pets_owned = 1
    
    db.session.commit()
    
    # Welcome message with pet introduction
    welcome_message = f"🎉 Welcome to your magical journey with {pet_name}! Your {pet_data['name']} is excited to learn and grow with you!"
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': welcome_message,
            'pet': {
                'name': pet_name,
                'type': pet_type,
                'species': pet_data['name'],
                'special': pet_data['special']
            },
            'redirect': '/dashboard'
        })
    
    flash(welcome_message)
    return redirect(url_for('main.dashboard'))

@auth_bp.route('/logout')
@login_required
def logout():
    # Update user stats before logout
    if current_user.pet_id:
        pet = Pet.query.get(current_user.pet_id)
        if pet:
            # Save current session data
            session_minutes = session.get('session_time', 0)
            current_user.total_study_time += session_minutes
            pet.experience += max(1, session_minutes // 5)  # XP for time spent
            
            # Update pet happiness based on interaction
            if session.get('pet_interactions', 0) > 0:
                pet.happiness = min(100, pet.happiness + 5)
    
    db.session.commit()
    logout_user()
    session.clear()
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/quick-mood-check', methods=['POST'])
@login_required
def quick_mood_check():
    """Quick mood assessment during login for personalized experience"""
    data = request.get_json()
    mood_text = data.get('mood_text', '')
    mood_emoji = data.get('mood_emoji', '😊')
    
    emotion_result = analyze_emotion(mood_text)
    
    # Update user's current mood
    current_user.current_mood = emotion_result['emotion']
    current_user.mood_score = emotion_result['confidence']
    db.session.commit()
    
    # Provide encouraging response based on mood
    responses = {
        'happy': "That's wonderful! Let's have an amazing learning adventure today! 🌟",
        'sad': "I understand you might be feeling down. Let's do some fun activities to brighten your day! 🌈",
        'angry': "It's okay to feel frustrated sometimes. Let's channel that energy into some exciting challenges! ⚡",
        'fear': "Don't worry, you're safe here! Let's start with some gentle, fun activities. 🛡️",
        'surprise': "What an interesting day! Let's explore and discover new things together! 🔍",
        'neutral': "Ready for a great learning session? Let's make today special! ✨"
    }
    
    return jsonify({
        'emotion': emotion_result['emotion'],
        'confidence': emotion_result['confidence'],
        'response': responses.get(emotion_result['emotion'], responses['neutral']),
        'suggested_activity': get_mood_appropriate_activity(emotion_result['emotion'])
    })

def get_mood_appropriate_activity(emotion):
    """Suggest activities based on user's emotional state"""
    activities = {
        'happy': 'challenging_quiz',
        'sad': 'creative_story',
        'angry': 'physical_game',
        'fear': 'guided_meditation',
        'surprise': 'exploration_quest',
        'neutral': 'balanced_learning'
    }
    return activities.get(emotion, 'balanced_learning')