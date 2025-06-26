from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timedelta
import os
import json
import random
import logging
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'eduhope_magical_learning_adventure_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eduhope.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = "🌟 Let's continue your magical learning journey!"
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import models and routes
from app.models.user import User, LearningSession,UserProgress
from app.models.pet import Pet
from app.models.pet_accessory import PetAccessory, UserPetAccessory
from app.models.lesson import Lesson, UserProgress, LessonFeedback
from app.models.achievement import Achievement, UserAchievement
from app.routes import auth, education, support, social, teacher, pet_companion, storytelling, language_games
from app.services.llm_service import LLMService
from app.services.voice_service import VoiceService
from app.services.sentiment_service import SentimentService
from app.assesment_games.knowledge_assesment import KnowledgeAssessmentGame
from app.assesment_games.emotional_assesment import EmotionalAssessmentGame

# Register blueprints
app.register_blueprint(auth.auth_bp)
app.register_blueprint(education.education_bp)
app.register_blueprint(support.support_bp)
app.register_blueprint(social.social_bp)
app.register_blueprint(teacher.teacher_bp)
app.register_blueprint(pet_companion.pet_bp)
app.register_blueprint(storytelling.storytelling_bp)
app.register_blueprint(language_games.language_games_bp)

# Initialize services
llm_service = LLMService()
voice_service = VoiceService()
sentiment_service = SentimentService()
knowledge_assessment = KnowledgeAssessmentGame()
emotional_assessment = EmotionalAssessmentGame()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Real-time learning analytics
class RealTimeLearning:
    def __init__(self):
        self.user_sessions = {}
        self.learning_patterns = {}
    
    def track_interaction(self, user_id, action, content_type, performance=None):
        """Track user interactions for real-time personalization"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'start_time': datetime.now(),
                'interactions': [],
                'performance_metrics': {},
                'learning_style': 'visual',  # Default
                'attention_span': 300,  # seconds
                'difficulty_preference': 'medium'
            }
        
        interaction = {
            'timestamp': datetime.now(),
            'action': action,
            'content_type': content_type,
            'performance': performance
        }
        
        self.user_sessions[user_id]['interactions'].append(interaction)
        self._analyze_learning_pattern(user_id)
        self._adapt_content_difficulty(user_id)
        
        # Save to database
        session_record = LearningSession(
            user_id=user_id,
            action=action,
            content_type=content_type,
            performance=performance,
            timestamp=datetime.now()
        )
        db.session.add(session_record)
        db.session.commit()
    
    def _analyze_learning_pattern(self, user_id):
        """Analyze user's learning patterns in real-time"""
        session = self.user_sessions[user_id]
        interactions = session['interactions']
        
        if len(interactions) < 5:
            return
        
        # Analyze response times
        response_times = []
        for i in range(1, len(interactions)):
            if interactions[i-1]['action'] == 'question_presented' and interactions[i]['action'] == 'answer_submitted':
                response_time = (interactions[i]['timestamp'] - interactions[i-1]['timestamp']).total_seconds()
                response_times.append(response_time)
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            session['attention_span'] = min(600, max(60, avg_response_time * 10))
        
        # Analyze performance patterns
        recent_performances = [i['performance'] for i in interactions[-10:] if i['performance'] is not None]
        if recent_performances:
            avg_performance = sum(recent_performances) / len(recent_performances)
            if avg_performance > 0.8:
                session['difficulty_preference'] = 'hard'
            elif avg_performance < 0.6:
                session['difficulty_preference'] = 'easy'
            else:
                session['difficulty_preference'] = 'medium'
    
    def _adapt_content_difficulty(self, user_id):
        """Adapt content difficulty based on performance"""
        session = self.user_sessions[user_id]
        user = User.query.get(user_id)
        
        if user:
            user.learning_style = session['learning_style']
            user.attention_span = session['attention_span']
            user.difficulty_preference = session['difficulty_preference']
            db.session.commit()
    
    def get_personalized_content(self, user_id, content_type):
        """Get personalized content recommendations"""
        if user_id not in self.user_sessions:
            return self._get_default_content(content_type)
        
        session = self.user_sessions[user_id]
        difficulty = session['difficulty_preference']
        learning_style = session['learning_style']
        
        # Query database for appropriate content
        query = Lesson.query.filter_by(content_type=content_type, difficulty=difficulty)
        
        if learning_style == 'visual':
            query = query.filter(Lesson.has_visuals == True)
        elif learning_style == 'auditory':
            query = query.filter(Lesson.has_audio == True)
        elif learning_style == 'kinesthetic':
            query = query.filter(Lesson.has_interactive_elements == True)
        
        return query.all()
    
    def _get_default_content(self, content_type):
        """Get default content for new users"""
        return Lesson.query.filter_by(content_type=content_type, difficulty='easy').limit(5).all()

# Initialize real-time learning
real_time_learning = RealTimeLearning()

@app.route('/')
def index():
    """Magical landing page for children"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    return render_template('index.html', 
                         magical_quotes=[
                             "🌟 Every day is a new adventure in learning!",
                             "🦄 Your imagination is your superpower!",
                             "🌈 Learning is like collecting magical treasures!",
                             "⭐ You're braver than you believe and smarter than you think!"
                         ])

@app.route('/dashboard')
@login_required
def dashboard():
    """Personalized dashboard with real-time adaptations"""
    user_pet = UserPetAccessory.query.filter_by(user_id=current_user.id, is_active=True).first()
    recent_achievements = UserAchievement.query.filter_by(user_id=current_user.id)\
                            .order_by(UserAchievement.earned_date.desc()).limit(3).all()
    
    # Get personalized content recommendations
    recommended_lessons = real_time_learning.get_personalized_content(current_user.id, 'lesson')
    
    # Calculate learning streak
    learning_streak = current_user.calculate_learning_streak()
    
    # Get mood-based recommendations
    current_mood = session.get('current_mood', 'happy')
    mood_activities = get_mood_based_activities(current_mood)
    
    return render_template('dashboard.html',
                         user_pet=user_pet,
                         recent_achievements=recent_achievements,
                         recommended_lessons=recommended_lessons,
                         learning_streak=learning_streak,
                         mood_activities=mood_activities,
                         current_mood=current_mood)

def get_mood_based_activities(mood):
    """Get activities based on child's emotional state"""
    activities = {
        'happy': [
            {'name': 'Math Adventure', 'icon': '🧮', 'type': 'lesson'},
            {'name': 'Story Creation', 'icon': '📚', 'type': 'creative'},
            {'name': 'Pet Playground', 'icon': '🐾', 'type': 'pet'}
        ],
        'sad': [
            {'name': 'Comfort Stories', 'icon': '🤗', 'type': 'story'},
            {'name': 'Breathing Buddy', 'icon': '🌸', 'type': 'wellness'},
            {'name': 'Pet Cuddles', 'icon': '💝', 'type': 'pet'}
        ],
        'excited': [
            {'name': 'Challenge Mode', 'icon': '⚡', 'type': 'challenge'},
            {'name': 'Group Adventures', 'icon': '👥', 'type': 'social'},
            {'name': 'Pet Training', 'icon': '🏆', 'type': 'pet'}
        ],
        'anxious': [
            {'name': 'Calm Corners', 'icon': '🧘', 'type': 'wellness'},
            {'name': 'Easy Puzzles', 'icon': '🧩', 'type': 'gentle'},
            {'name': 'Pet Meditation', 'icon': '🕯️', 'type': 'pet'}
        ]
    }
    return activities.get(mood, activities['happy'])

@app.route('/api/track_interaction', methods=['POST'])
@login_required
def track_interaction():
    """API endpoint for tracking user interactions"""
    data = request.get_json()
    
    real_time_learning.track_interaction(
        user_id=current_user.id,
        action=data.get('action'),
        content_type=data.get('content_type'),
        performance=data.get('performance')
    )
    
    return jsonify({'status': 'tracked'})

@app.route('/api/personalized_content/<content_type>')
@login_required
def get_personalized_content_api(content_type):
    """API endpoint for getting personalized content"""
    content = real_time_learning.get_personalized_content(current_user.id, content_type)
    
    return jsonify([{
        'id': item.id,
        'title': item.title,
        'description': item.description,
        'difficulty': item.difficulty,
        'estimated_time': item.estimated_time
    } for item in content])

# Socket.IO events for real-time features
@socketio.on('join_learning_session')
def on_join_learning_session(data):
    """Handle user joining learning session"""
    room = f"learning_{current_user.id}"
    join_room(room)
    emit('session_joined', {'room': room})

@socketio.on('learning_progress')
def on_learning_progress(data):
    """Handle real-time learning progress updates"""
    real_time_learning.track_interaction(
        user_id=current_user.id,
        action=data.get('action'),
        content_type=data.get('content_type'),
        performance=data.get('performance')
    )
    
    # Send adaptive feedback
    room = f"learning_{current_user.id}"
    emit('adaptive_feedback', {
        'encouragement': get_adaptive_encouragement(data.get('performance')),
        'next_suggestion': get_next_suggestion(current_user.id)
    }, room=room)

def get_adaptive_encouragement(performance):
    """Get encouraging messages based on performance"""
    if performance and performance > 0.8:
        return random.choice([
            "🌟 You're absolutely brilliant!",
            "🦄 That was magical! Keep going!",
            "⭐ You're a learning superstar!",
            "🌈 Amazing work, champion!"
        ])
    elif performance and performance > 0.6:
        return random.choice([
            "🌱 Great effort! You're growing stronger!",
            "🎯 Good job! Keep practicing!",
            "💪 You're doing wonderful!",
            "🌟 Nice work! Learning takes courage!"
        ])
    else:
        return random.choice([
            "🤗 It's okay! Every mistake helps us learn!",
            "🌈 You're brave for trying! Let's try again!",
            "💝 Learning is a journey, not a race!",
            "⭐ I believe in you! You've got this!"
        ])

def get_next_suggestion(user_id):
    """Get next learning suggestion"""
    suggestions = real_time_learning.get_personalized_content(user_id, 'lesson')
    if suggestions:
        return {
            'title': suggestions[0].title,
            'description': suggestions[0].description,
            'url': f'/lesson/{suggestions[0].id}'
        }
    return None

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code=404,
                         error_message="🔍 Oops! This magical page seems to be hiding!",
                         suggestion="Let's go back to your dashboard and continue learning!"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html',
                         error_code=500,
                         error_message="🛠️ Our magical workshop is having a tiny problem!",
                         suggestion="Don't worry! Our coding wizards are fixing it. Try again in a moment!"), 500

# Database initialization
# @app.before_first_request 
def create_tables():
    """Initialize database tables and sample data"""
    db.create_all()
    
    # Create sample pets if not exist
    if Pet.query.count() == 0:
        create_fantasy_pets()
    
    # Create sample lessons if not exist
    if Lesson.query.count() == 0:
        create_sample_lessons()
    
    # Create achievements if not exist
    if Achievement.query.count() == 0:
        create_achievements()

def create_fantasy_pets():
    """Create 20+ fantasy pets for children to choose from"""
    fantasy_pets = [
        {'name': 'Sparkle Dragon', 'type': 'dragon', 'description': 'A magical dragon that breathes rainbow sparkles!', 'emoji': '🐲', 'rarity': 'legendary'},
        {'name': 'Crystal Unicorn', 'type': 'unicorn', 'description': 'A beautiful unicorn with a crystal horn that grants wishes!', 'emoji': '🦄', 'rarity': 'legendary'},
        {'name': 'Cosmic Phoenix', 'type': 'phoenix', 'description': 'A phoenix that flies among the stars!', 'emoji': '🔥', 'rarity': 'legendary'},
        {'name': 'Rainbow Butterfly', 'type': 'butterfly', 'description': 'A butterfly with wings that shimmer like rainbows!', 'emoji': '🦋', 'rarity': 'rare'},
        {'name': 'Cloud Elephant', 'type': 'elephant', 'description': 'A fluffy elephant that floats on clouds!', 'emoji': '☁️', 'rarity': 'rare'},
        {'name': 'Starlight Fox', 'type': 'fox', 'description': 'A fox with fur that twinkles like stars!', 'emoji': '🦊', 'rarity': 'rare'},
        {'name': 'Ocean Dolphin', 'type': 'dolphin', 'description': 'A wise dolphin from the deepest oceans!', 'emoji': '🐬', 'rarity': 'common'},
        {'name': 'Forest Wolf', 'type': 'wolf', 'description': 'A loyal wolf guardian of magical forests!', 'emoji': '🐺', 'rarity': 'common'},
        {'name': 'Golden Eagle', 'type': 'eagle', 'description': 'A majestic eagle with golden feathers!', 'emoji': '🦅', 'rarity': 'common'},
        {'name': 'Crystal Turtle', 'type': 'turtle', 'description': 'An ancient turtle with a crystal shell!', 'emoji': '🐢', 'rarity': 'rare'},
        {'name': 'Fire Salamander', 'type': 'salamander', 'description': 'A salamander that controls magical flames!', 'emoji': '🦎', 'rarity': 'rare'},
        {'name': 'Ice Penguin', 'type': 'penguin', 'description': 'A penguin from the magical ice kingdoms!', 'emoji': '🐧', 'rarity': 'common'},
        {'name': 'Thunder Lion', 'type': 'lion', 'description': 'A brave lion with a thunderous roar!', 'emoji': '🦁', 'rarity': 'rare'},
        {'name': 'Wind Hawk', 'type': 'hawk', 'description': 'A swift hawk that rides the wind!', 'emoji': '🦅', 'rarity': 'common'},
        {'name': 'Dream Owl', 'type': 'owl', 'description': 'A wise owl that protects dreams!', 'emoji': '🦉', 'rarity': 'rare'},
        {'name': 'Moon Rabbit', 'type': 'rabbit', 'description': 'A rabbit that hops on moonbeams!', 'emoji': '🐰', 'rarity': 'common'},
        {'name': 'Solar Bear', 'type': 'bear', 'description': 'A cuddly bear powered by sunshine!', 'emoji': '🐻', 'rarity': 'common'},
        {'name': 'Mystic Cat', 'type': 'cat', 'description': 'A mysterious cat with magical powers!', 'emoji': '🐱', 'rarity': 'common'},
        {'name': 'Cyber Robot', 'type': 'robot', 'description': 'A friendly robot from the future!', 'emoji': '🤖', 'rarity': 'rare'},
        {'name': 'Nature Fairy', 'type': 'fairy', 'description': 'A tiny fairy that cares for nature!', 'emoji': '🧚', 'rarity': 'legendary'},
        {'name': 'Space Alien', 'type': 'alien', 'description': 'A curious alien explorer from distant stars!', 'emoji': '👽', 'rarity': 'rare'},
        {'name': 'Magic Mushroom', 'type': 'mushroom', 'description': 'A sentient mushroom from enchanted forests!', 'emoji': '🍄', 'rarity': 'common'},
        {'name': 'Shadow Ninja', 'type': 'ninja', 'description': 'A stealthy ninja companion!', 'emoji': '🥷', 'rarity': 'rare'},
        {'name': 'Gem Collector', 'type': 'collector', 'description': 'A creature that loves shiny gems!', 'emoji': '💎', 'rarity': 'common'}
    ]
    
    for pet_data in fantasy_pets:
        pet = Pet(**pet_data)
        db.session.add(pet)
    
    db.session.commit()

def create_sample_lessons():
    """Create sample lessons for different subjects"""
    lessons = [
        {
            'title': '🧮 Magic Numbers Adventure',
            'description': 'Learn addition with magical creatures!',
            'content_type': 'math',
            'difficulty': 'easy',
            'age_group': '5-7',
            'estimated_time': 15,
            'has_visuals': True,
            'has_audio': True,
            'has_interactive_elements': True,
            'content': json.dumps({
                'introduction': 'Welcome to the magical numbers kingdom!',
                'activities': [
                    {'type': 'interactive', 'title': 'Count the Dragons', 'description': 'Help the dragons find their treasure!'},
                    {'type': 'quiz', 'question': 'How many unicorns do you see?', 'options': ['2', '3', '4'], 'correct': 1}
                ]
            })
        },
        {
            'title': '📚 Story Time Adventures',
            'description': 'Create magical stories with friends!',
            'content_type': 'language',
            'difficulty': 'medium',
            'age_group': '6-9',
            'estimated_time': 20,
            'has_visuals': True,
            'has_audio': True,
            'has_interactive_elements': True,
            'content': json.dumps({
                'introduction': 'Every story begins with once upon a time...',
                'prompts': [
                    'A dragon who was afraid of flying...',
                    'A princess who loved to code...',
                    'A robot who wanted to paint...'
                ]
            })
        }
    ]
    
    for lesson_data in lessons:
        lesson = Lesson(**lesson_data)
        db.session.add(lesson)
    
    db.session.commit()

def create_achievements():
    """Create achievement badges for gamification"""
    achievements = [
        {'name': 'First Steps', 'description': 'Completed your first lesson!', 'icon': '👶', 'points': 10},
        {'name': 'Pet Parent', 'description': 'Adopted your first magical pet!', 'icon': '🏠', 'points': 20},
        {'name': 'Quick Learner', 'description': 'Completed 5 lessons in one day!', 'icon': '⚡', 'points': 50},
        {'name': 'Story Master', 'description': 'Created 10 amazing stories!', 'icon': '📖', 'points': 100},
        {'name': 'Math Wizard', 'description': 'Solved 50 math problems!', 'icon': '🧙', 'points': 75},
        {'name': 'Caring Friend', 'description': 'Helped 5 friends with their pets!', 'icon': '💝', 'points': 40},
        {'name': 'Explorer', 'description': 'Tried all different types of lessons!', 'icon': '🗺️', 'points': 60},
        {'name': 'Champion', 'description': 'Maintained a 30-day learning streak!', 'icon': '🏆', 'points': 200}
    ]
    
    for achievement_data in achievements:
        achievement = Achievement(**achievement_data)
        db.session.add(achievement)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    
    print("🌟 EduHope Magical Learning Platform Starting! 🌟")
    print("🦄 Where every child's learning journey becomes an adventure! 🦄")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)