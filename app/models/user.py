from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Enhanced User model with real-time learning capabilities"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Personal Information
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    birthday = db.Column(db.Date)
    gender = db.Column(db.String(20))
    preferred_language = db.Column(db.String(20), default='en')
    
    # Learning Profile - Real-time Adaptation
    learning_style = db.Column(db.String(20), default='visual')  # visual, auditory, kinesthetic, mixed
    attention_span = db.Column(db.Integer, default=300)  # seconds
    difficulty_preference = db.Column(db.String(20), default='medium')  # easy, medium, hard
    preferred_subjects = db.Column(db.Text)  # JSON string of preferred subjects
    learning_pace = db.Column(db.String(20), default='moderate')  # slow, moderate, fast
    
    # Emotional Profile
    current_mood = db.Column(db.String(20), default='happy')
    emotional_state_history = db.Column(db.Text)  # JSON string of mood tracking
    support_level_needed = db.Column(db.String(20), default='low')  # low, medium, high
    
    # Gamification & Progress
    total_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    experience_points = db.Column(db.Integer, default=0)
    learning_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    
    # Engagement Metrics
    total_lessons_completed = db.Column(db.Integer, default=0)
    total_time_spent = db.Column(db.Integer, default=0)  # minutes
    favorite_activities = db.Column(db.Text)  # JSON string
    last_active = db.Column(db.DateTime, default=datetime.now)
    
    # Account Management
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)
    
    # Parental Controls & Safety
    parental_email = db.Column(db.String(120))
    content_filter_level = db.Column(db.String(20), default='child_safe')
    chat_permissions = db.Column(db.Boolean, default=True)
    
    # Adaptive Learning Weights
    visual_learning_weight = db.Column(db.Float, default=0.33)
    auditory_learning_weight = db.Column(db.Float, default=0.33)
    kinesthetic_learning_weight = db.Column(db.Float, default=0.34)
    
    # Relationships
    pets = db.relationship('UserPet', backref='owner', lazy=True, cascade='all, delete-orphan')
    achievements = db.relationship('UserAchievement', backref='user', lazy=True, cascade='all, delete-orphan')
    quiz_attempts = db.relationship('UserQuizAttempt', backref='user', lazy=True, cascade='all, delete-orphan')
    learning_sessions = db.relationship('LearningSession', backref='user', lazy=True, cascade='all, delete-orphan')
    progress_records = db.relationship('UserProgress', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, username, email, full_name, age, password=None):
        self.username = username
        self.email = email
        self.full_name = full_name
        self.age = age
        self.preferred_subjects = json.dumps(['math', 'reading', 'science'])
        self.emotional_state_history = json.dumps([])
        self.favorite_activities = json.dumps([])
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    # Real-time Learning Adaptation Methods
    def update_learning_style_weights(self, interaction_data):
        """Update learning style weights based on real-time performance"""
        performance_by_style = {
            'visual': [],
            'auditory': [],
            'kinesthetic': []
        }
        
        # Analyze recent interactions
        for interaction in interaction_data[-20:]:  # Last 20 interactions
            if interaction.get('content_style') and interaction.get('performance'):
                style = interaction['content_style']
                performance = interaction['performance']
                if style in performance_by_style:
                    performance_by_style[style].append(performance)
        
        # Calculate new weights based on performance
        total_weight = 0
        for style, performances in performance_by_style.items():
            if performances:
                avg_performance = sum(performances) / len(performances)
                if style == 'visual':
                    self.visual_learning_weight = max(0.1, min(0.7, avg_performance))
                elif style == 'auditory':
                    self.auditory_learning_weight = max(0.1, min(0.7, avg_performance))
                elif style == 'kinesthetic':
                    self.kinesthetic_learning_weight = max(0.1, min(0.7, avg_performance))
        
        # Normalize weights
        total = self.visual_learning_weight + self.auditory_learning_weight + self.kinesthetic_learning_weight
        if total > 0:
            self.visual_learning_weight /= total
            self.auditory_learning_weight /= total
            self.kinesthetic_learning_weight /= total
    
    def get_dominant_learning_style(self):
        """Get the dominant learning style based on current weights"""
        weights = {
            'visual': self.visual_learning_weight,
            'auditory': self.auditory_learning_weight,
            'kinesthetic': self.kinesthetic_learning_weight
        }
        return max(weights, key=weights.get)
    
    def update_emotional_state(self, new_mood, context=None):
        """Update emotional state with history tracking"""
        emotion_entry = {
            'mood': new_mood,
            'timestamp': datetime.now().isoformat(),
            'context': context
        }
        
        history = json.loads(self.emotional_state_history or '[]')
        history.append(emotion_entry)
        
        # Keep only last 100 entries
        if len(history) > 100:
            history = history[-100:]
        
        self.emotional_state_history = json.dumps(history)
        self.current_mood = new_mood
        
        # Adjust support level based on emotional patterns
        self._analyze_emotional_patterns()
    
    def _analyze_emotional_patterns(self):
        """Analyze emotional patterns to adjust support level"""
        history = json.loads(self.emotional_state_history or '[]')
        if len(history) < 5:
            return
        
        recent_moods = [entry['mood'] for entry in history[-10:]]
        negative_moods = ['sad', 'anxious', 'frustrated', 'angry', 'overwhelmed']
        
        negative_count = sum(1 for mood in recent_moods if mood in negative_moods)
        
        if negative_count >= 7:
            self.support_level_needed = 'high'
        elif negative_count >= 4:
            self.support_level_needed = 'medium'
        else:
            self.support_level_needed = 'low'
    
    def get_emotional_insights(self):
        """Get insights about emotional patterns"""
        history = json.loads(self.emotional_state_history or '[]')
        if not history:
            return {'dominant_mood': 'happy', 'stability': 'stable', 'trend': 'positive'}
        
        recent_moods = [entry['mood'] for entry in history[-20:]]
        mood_counts = {}
        for mood in recent_moods:
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        dominant_mood = max(mood_counts, key=mood_counts.get) if mood_counts else 'happy'
        
        # Calculate stability (how often mood changes)
        changes = 0
        for i in range(1, len(recent_moods)):
            if recent_moods[i] != recent_moods[i-1]:
                changes += 1
        
        stability = 'stable' if changes <= 3 else 'moderate' if changes <= 6 else 'volatile'
        
        # Determine trend
        positive_moods = ['happy', 'excited', 'confident', 'curious', 'proud']
        recent_positive = sum(1 for mood in recent_moods[-5:] if mood in positive_moods)
        trend = 'positive' if recent_positive >= 3 else 'negative' if recent_positive <= 1 else 'neutral'
        
        return {
            'dominant_mood': dominant_mood,
            'stability': stability,
            'trend': trend,
            'mood_distribution': mood_counts
        }
    
    def add_experience_points(self, points, activity_type=None):
        """Add experience points and handle level ups"""
        self.experience_points += points
        self.total_points += points
        
        # Level up calculation (exponential growth)
        required_xp = (self.level ** 2) * 100
        
        leveled_up = False
        while self.experience_points >= required_xp:
            self.level += 1
            self.experience_points -= required_xp
            required_xp = (self.level ** 2) * 100
            leveled_up = True
        
        if leveled_up:
            self._handle_level_up()
        
        return leveled_up
    
    def _handle_level_up(self):
        """Handle level up rewards and notifications"""
        # Add level-up achievement if applicable
        from models.achievement import Achievement, UserAchievement
        
        level_achievements = {
            5: 'Rising Star',
            10: 'Learning Champion',
            15: 'Knowledge Seeker',
            20: 'Wisdom Master',
            25: 'Learning Legend'
        }
        
        if self.level in level_achievements:
            achievement_name = level_achievements[self.level]
            achievement = Achievement.query.filter_by(name=achievement_name).first()
            if achievement:
                existing = UserAchievement.query.filter_by(
                    user_id=self.id, 
                    achievement_id=achievement.id
                ).first()
                if not existing:
                    user_achievement = UserAchievement(
                        user_id=self.id,
                        achievement_id=achievement.id,
                        earned_date=datetime.now()
                    )
                    db.session.add(user_achievement)
    
    def update_learning_streak(self):
        """Update learning streak based on activity"""
        today = datetime.now().date()
        
        # Check if user was active yesterday
        yesterday = today - timedelta(days=1)
        yesterday_sessions = LearningSession.query.filter(
            LearningSession.user_id == self.id,
            LearningSession.timestamp >= yesterday,
            LearningSession.timestamp < today
        ).count()
        
        # Check if user is active today
        today_sessions = LearningSession.query.filter(
            LearningSession.user_id == self.id,
            LearningSession.timestamp >= today
        ).count()
        
        if today_sessions > 0:
            if yesterday_sessions > 0:
                self.learning_streak += 1
            else:
                self.learning_streak = 1
            
            if self.learning_streak > self.longest_streak:
                self.longest_streak = self.learning_streak
        elif yesterday_sessions == 0:
            self.learning_streak = 0
    
    def calculate_learning_streak(self):
        """Calculate current learning streak"""
        today = datetime.now().date()
        streak = 0
        
        current_date = today
        while True:
            sessions = LearningSession.query.filter(
                LearningSession.user_id == self.id,
                LearningSession.timestamp >= current_date,
                LearningSession.timestamp < current_date + timedelta(days=1)
            ).count()
            
            if sessions > 0:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
                
            # Limit to prevent infinite loops
            if streak > 365:
                break
        
        return streak
    
    def get_preferred_subjects(self):
        """Get list of preferred subjects"""
        return json.loads(self.preferred_subjects or '["math", "reading", "science"]')
    
    def update_preferred_subjects(self, subjects):
        """Update preferred subjects"""
        self.preferred_subjects = json.dumps(subjects)
    
    def get_favorite_activities(self):
        """Get list of favorite activities"""
        return json.loads(self.favorite_activities or '[]')
    
    def update_favorite_activities(self, activities):
        """Update favorite activities"""
        self.favorite_activities = json.dumps(activities)
    
    def get_personalized_recommendations(self):
        """Get personalized learning recommendations"""
        recommendations = {
            'difficulty': self.difficulty_preference,
            'learning_style': self.get_dominant_learning_style(),
            'subjects': self.get_preferred_subjects(),
            'emotional_support': self.support_level_needed,
            'session_length': min(self.attention_span // 60, 30)  # Convert to minutes, max 30
        }
        
        # Adjust based on current mood
        mood_adjustments = {
            'sad': {'difficulty': 'easy', 'support': 'high'},
            'anxious': {'difficulty': 'easy', 'support': 'high', 'session_length': 10},
            'frustrated': {'difficulty': 'easy', 'support': 'medium'},
            'excited': {'difficulty': 'hard', 'session_length': 25},
            'confident': {'difficulty': 'hard'}
        }
        
        if self.current_mood in mood_adjustments:
            adjustments = mood_adjustments[self.current_mood]
            recommendations.update(adjustments)
        
        return recommendations
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'age': self.age,
            'level': self.level,
            'total_points': self.total_points,
            'learning_streak': self.calculate_learning_streak(),
            'learning_style': self.get_dominant_learning_style(),
            'current_mood': self.current_mood,
            'preferred_subjects': self.get_preferred_subjects(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class LearningSession(db.Model):
    """Track individual learning sessions for real-time adaptation"""
    __tablename__ = 'learning_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # lesson_start, question_answered, etc.
    content_type = db.Column(db.String(50), nullable=False)  # math, reading, science, etc.
    content_id = db.Column(db.Integer)  # ID of lesson, quiz, etc.
    performance = db.Column(db.Float)  # 0.0 to 1.0 performance score
    response_time = db.Column(db.Float)  # Time taken in seconds
    emotional_state = db.Column(db.String(20))  # User's mood during session
    difficulty_level = db.Column(db.String(20))  # easy, medium, hard
    learning_style_used = db.Column(db.String(20))  # visual, auditory, kinesthetic
    timestamp = db.Column(db.DateTime, default=datetime.now)
    session_duration = db.Column(db.Integer)  # Duration in seconds
    
    # Analysis fields
    attention_level = db.Column(db.String(20))  # high, medium, low
    engagement_score = db.Column(db.Float)  # 0.0 to 1.0
    help_requests = db.Column(db.Integer, default=0)
    completion_status = db.Column(db.String(20))  # completed, incomplete, skipped
    
    def __init__(self, user_id, action, content_type, **kwargs):
        self.user_id = user_id
        self.action = action
        self.content_type = content_type
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

class UserProgress(db.Model):
    """Track detailed progress across different subjects and skills"""
    __tablename__ = 'user_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)  # math, reading, science, etc.
    skill = db.Column(db.String(100), nullable=False)  # addition, phonics, etc.
    current_level = db.Column(db.Integer, default=1)
    mastery_score = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    attempts = db.Column(db.Integer, default=0)
    successes = db.Column(db.Integer, default=0)
    
    # Adaptive tracking
    optimal_difficulty = db.Column(db.String(20), default='medium')
    learning_velocity = db.Column(db.Float, default=1.0)  # How fast they learn this skill
    retention_rate = db.Column(db.Float, default=0.8)  # How well they retain knowledge
    
    # Timestamps
    first_attempt = db.Column(db.DateTime, default=datetime.now)
    last_attempt = db.Column(db.DateTime, default=datetime.now)
    mastery_achieved = db.Column(db.DateTime)
    
    # Constraints
    __table_args__ = (db.UniqueConstraint('user_id', 'subject', 'skill'),)
    
    def update_progress(self, success, difficulty='medium'):
        """Update progress based on attempt outcome"""
        self.attempts += 1
        if success:
            self.successes += 1
        
        # Calculate new mastery score
        success_rate = self.successes / self.attempts
        self.mastery_score = min(1.0, success_rate * 1.2)  # Boost for consistency
        
        # Update optimal difficulty
        if success_rate > 0.85 and difficulty == 'easy':
            self.optimal_difficulty = 'medium'
        elif success_rate > 0.85 and difficulty == 'medium':
            self.optimal_difficulty = 'hard'
        elif success_rate < 0.6 and difficulty == 'hard':
            self.optimal_difficulty = 'medium'
        elif success_rate < 0.4 and difficulty == 'medium':
            self.optimal_difficulty = 'easy'
        
        # Calculate learning velocity
        time_since_first = (datetime.now() - self.first_attempt).total_seconds() / 3600  # hours
        if time_since_first > 0:
            self.learning_velocity = self.mastery_score / time_since_first
        
        # Check for mastery
        if self.mastery_score >= 0.9 and not self.mastery_achieved:
            self.mastery_achieved = datetime.now()
        
        self.last_attempt = datetime.now()
    
    def get_next_recommendation(self):
        """Get recommendation for next learning activity"""
        if self.mastery_score < 0.3:
            return {
                'action': 'practice_basics',
                'difficulty': 'easy',
                'focus': 'foundation_building'
            }
        elif self.mastery_score < 0.7:
            return {
                'action': 'guided_practice',
                'difficulty': self.optimal_difficulty,
                'focus': 'skill_building'
            }
        else:
            return {
                'action': 'challenge_mode',
                'difficulty': 'hard',
                'focus': 'mastery_verification'
            }