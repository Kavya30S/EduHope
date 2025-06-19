from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import random
import json

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'eduhope-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eduhope.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access EduHope!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Import all models
from models.user import User
from models.pet import Pet
from models.lesson import Lesson
from models.achievement import Achievement
from models.story import Story

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            
            # Check if user needs to select a pet
            if not user.pet:
                return redirect(url_for('select_pet'))
            
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        age = int(request.form['age'])
        language = request.form['language']
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            age=age,
            language=language
        )
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('assessment_games'))
    
    return render_template('register.html')

@app.route('/assessment_games')
@login_required
def assessment_games():
    return render_template('assessment_games.html')

@app.route('/select_pet')
@login_required
def select_pet():
    if current_user.pet:
        return redirect(url_for('dashboard'))
    
    # Available pets with their characteristics
    available_pets = [
        {'id': 'dragon', 'name': 'Dragon', 'description': 'Fierce and loyal, dragons love solving math puzzles!', 'image': 'dragon.png'},
        {'id': 'unicorn', 'name': 'Unicorn', 'description': 'Magical and gentle, unicorns excel at language learning!', 'image': 'unicorn.png'},
        {'id': 'robot', 'name': 'Robot', 'description': 'Smart and curious, robots are perfect for science adventures!', 'image': 'robot.png'},
        {'id': 'phoenix', 'name': 'Phoenix', 'description': 'Wise and creative, phoenixes love storytelling!', 'image': 'phoenix.png'},
        {'id': 'cat', 'name': 'Magic Cat', 'description': 'Playful and mysterious, cats are great at all subjects!', 'image': 'cat.png'}
    ]
    
    return render_template('select_pet.html', pets=available_pets)

@app.route('/choose_pet', methods=['POST'])
@login_required
def choose_pet():
    pet_type = request.form['pet_type']
    pet_name = request.form['pet_name']
    
    # Create new pet for user
    pet = Pet(
        user_id=current_user.id,
        pet_type=pet_type,
        name=pet_name,
        happiness=100,
        hunger=50,
        energy=100,
        level=1,
        experience=0
    )
    
    db.session.add(pet)
    db.session.commit()
    
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_stats = {
        'total_points': current_user.points,
        'level': current_user.level,
        'achievements_count': len(current_user.achievements),
        'lessons_completed': current_user.lessons_completed
    }
    
    # Get pet stats if exists
    pet_stats = None
    if current_user.pet:
        pet_stats = {
            'name': current_user.pet.name,
            'type': current_user.pet.pet_type,
            'level': current_user.pet.level,
            'happiness': current_user.pet.happiness,
            'hunger': current_user.pet.hunger,
            'energy': current_user.pet.energy,
            'experience': current_user.pet.experience
        }
    
    return render_template('dashboard.html', user_stats=user_stats, pet_stats=pet_stats)

@app.route('/pet')
@login_required
def pet_page():
    if not current_user.pet:
        return redirect(url_for('select_pet'))
    
    pet = current_user.pet
    return render_template('pet.html', pet=pet)

@app.route('/feed_pet', methods=['POST'])
@login_required
def feed_pet():
    if not current_user.pet:
        return jsonify({'error': 'No pet found'}), 400
    
    pet = current_user.pet
    
    # Check if user has enough points
    food_cost = 10
    if current_user.points < food_cost:
        return jsonify({'error': 'Not enough points to feed pet'}), 400
    
    # Feed the pet
    pet.hunger = min(100, pet.hunger + 20)
    pet.happiness = min(100, pet.happiness + 10)
    pet.last_fed = datetime.utcnow()
    
    # Deduct points
    current_user.points -= food_cost
    
    # Add experience
    pet.experience += 5
    if pet.experience >= pet.level * 100:
        pet.level += 1
        pet.experience = 0
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'pet': {
            'hunger': pet.hunger,
            'happiness': pet.happiness,
            'level': pet.level,
            'experience': pet.experience
        },
        'user_points': current_user.points
    })

@app.route('/play_with_pet', methods=['POST'])
@login_required
def play_with_pet():
    if not current_user.pet:
        return jsonify({'error': 'No pet found'}), 400
    
    pet = current_user.pet
    
    # Check if pet has enough energy
    if pet.energy < 20:
        return jsonify({'error': 'Pet is too tired to play'}), 400
    
    # Play with pet
    pet.happiness = min(100, pet.happiness + 15)
    pet.energy = max(0, pet.energy - 20)
    pet.last_played = datetime.utcnow()
    
    # Add experience
    pet.experience += 10
    if pet.experience >= pet.level * 100:
        pet.level += 1
        pet.experience = 0
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'pet': {
            'happiness': pet.happiness,
            'energy': pet.energy,
            'level': pet.level,
            'experience': pet.experience
        }
    })

@app.route('/lessons')
@login_required
def lessons():
    # Get lessons based on user's age and level
    user_lessons = Lesson.query.filter(
        Lesson.min_age <= current_user.age,
        Lesson.max_age >= current_user.age
    ).all()
    
    return render_template('lessons.html', lessons=user_lessons)

@app.route('/lesson/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    return render_template('lesson_detail.html', lesson=lesson)

@app.route('/complete_lesson', methods=['POST'])
@login_required
def complete_lesson():
    lesson_id = request.json['lesson_id']
    score = request.json['score']
    
    # Award points based on score
    points_earned = score * 10
    current_user.points += points_earned
    current_user.lessons_completed += 1
    
    # Feed pet automatically on lesson completion
    if current_user.pet:
        current_user.pet.hunger = min(100, current_user.pet.hunger + 10)
        current_user.pet.happiness = min(100, current_user.pet.happiness + 5)
        current_user.pet.experience += points_earned // 2
        
        if current_user.pet.experience >= current_user.pet.level * 100:
            current_user.pet.level += 1
            current_user.pet.experience = 0
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'points_earned': points_earned,
        'total_points': current_user.points
    })

@app.route('/games')
@login_required
def games():
    return render_template('games.html')

@app.route('/math_maze')
@login_required
def math_maze():
    return render_template('math_maze.html')

@app.route('/language_games')
@login_required
def language_games():
    return render_template('language_games.html')

@app.route('/storytelling')
@login_required
def storytelling():
    stories = Story.query.filter_by(is_public=True).order_by(Story.created_at.desc()).limit(10).all()
    return render_template('storytelling.html', stories=stories)

@app.route('/create_story', methods=['POST'])
@login_required
def create_story():
    title = request.json['title']
    content = request.json['content']
    
    story = Story(
        title=title,
        content=content,
        author_id=current_user.id,
        is_public=True
    )
    
    db.session.add(story)
    db.session.commit()
    
    # Award points for creativity
    current_user.points += 25
    
    # Feed pet for creative activity
    if current_user.pet:
        current_user.pet.happiness = min(100, current_user.pet.happiness + 10)
        current_user.pet.experience += 15
        
        if current_user.pet.experience >= current_user.pet.level * 100:
            current_user.pet.level += 1
            current_user.pet.experience = 0
    
    db.session.commit()
    
    return jsonify({'success': True, 'story_id': story.id})

@app.route('/achievements')
@login_required
def achievements():
    user_achievements = current_user.achievements
    return render_template('achievements.html', achievements=user_achievements)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# SocketIO events for real-time features
@socketio.on('join_room')
def handle_join_room(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'{current_user.username} has joined the room.'}, room=room)

@socketio.on('leave_room')
def handle_leave_room(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'{current_user.username} has left the room.'}, room=room)

@socketio.on('story_update')
def handle_story_update(data):
    room = data['room']
    content = data['content']
    emit('story_content', {'content': content, 'author': current_user.username}, room=room)

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create sample lessons if they don't exist
        if not Lesson.query.first():
            sample_lessons = [
                Lesson(
                    title="Basic Math - Addition",
                    description="Learn to add numbers with fun examples!",
                    content="Let's learn addition with colorful examples and pet rewards!",
                    subject="Math",
                    min_age=5,
                    max_age=8,
                    difficulty=1
                ),
                Lesson(
                    title="English Alphabet Adventure",
                    description="Explore letters with your pet companion!",
                    content="Join your pet on an alphabet adventure!",
                    subject="English",
                    min_age=4,
                    max_age=7,
                    difficulty=1
                ),
                Lesson(
                    title="Science Wonders",
                    description="Discover amazing science facts!",
                    content="Explore the world of science with interactive experiments!",
                    subject="Science",
                    min_age=6,
                    max_age=10,
                    difficulty=2
                )
            ]
            
            for lesson in sample_lessons:
                db.session.add(lesson)
            
            db.session.commit()

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)