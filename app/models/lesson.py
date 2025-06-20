from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    age_group = db.Column(db.String(50), nullable=False)  # 4-6, 7-9, 10-12, 13-15
    difficulty_level = db.Column(db.Integer, default=1)  # 1-5 scale
    content = db.Column(db.Text, nullable=False)
    interactive_elements = db.Column(db.Text)  # JSON string for games/activities
    rewards = db.Column(db.Text)  # JSON string for pet rewards
    learning_objectives = db.Column(db.Text)  # JSON array of objectives
    estimated_time = db.Column(db.Integer, default=15)  # minutes
    prerequisite_lessons = db.Column(db.Text)  # JSON array of lesson IDs
    multimedia_content = db.Column(db.Text)  # JSON for videos, images, sounds
    
    # AI Personalization fields
    adaptation_data = db.Column(db.Text)  # JSON for AI adaptation insights
    engagement_metrics = db.Column(db.Text)  # JSON for tracking engagement
    
    # Emotional learning support
    emotional_tone = db.Column(db.String(50), default='neutral')  # happy, calm, encouraging
    mindfulness_elements = db.Column(db.Text)  # JSON for breathing exercises, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_progress = db.relationship('UserProgress', backref='lesson', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, title, subject, age_group, content, **kwargs):
        self.title = title
        self.subject = subject
        self.age_group = age_group
        self.content = content
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert lesson to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'subject': self.subject,
            'age_group': self.age_group,
            'difficulty_level': self.difficulty_level,
            'content': self.content,
            'interactive_elements': json.loads(self.interactive_elements) if self.interactive_elements else [],
            'rewards': json.loads(self.rewards) if self.rewards else {},
            'learning_objectives': json.loads(self.learning_objectives) if self.learning_objectives else [],
            'estimated_time': self.estimated_time,
            'prerequisite_lessons': json.loads(self.prerequisite_lessons) if self.prerequisite_lessons else [],
            'multimedia_content': json.loads(self.multimedia_content) if self.multimedia_content else {},
            'adaptation_data': json.loads(self.adaptation_data) if self.adaptation_data else {},
            'engagement_metrics': json.loads(self.engagement_metrics) if self.engagement_metrics else {},
            'emotional_tone': self.emotional_tone,
            'mindfulness_elements': json.loads(self.mindfulness_elements) if self.mindfulness_elements else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_interactive_elements(self):
        """Get parsed interactive elements"""
        if self.interactive_elements:
            return json.loads(self.interactive_elements)
        return []
    
    def set_interactive_elements(self, elements):
        """Set interactive elements from dict/list"""
        self.interactive_elements = json.dumps(elements)
    
    def get_rewards(self):
        """Get parsed rewards"""
        if self.rewards:
            return json.loads(self.rewards)
        return {}
    
    def set_rewards(self, rewards):
        """Set rewards from dict"""
        self.rewards = json.dumps(rewards)
    
    def get_learning_objectives(self):
        """Get parsed learning objectives"""
        if self.learning_objectives:
            return json.loads(self.learning_objectives)
        return []
    
    def set_learning_objectives(self, objectives):
        """Set learning objectives from list"""
        self.learning_objectives = json.dumps(objectives)
    
    def get_multimedia_content(self):
        """Get parsed multimedia content"""
        if self.multimedia_content:
            return json.loads(self.multimedia_content)
        return {}
    
    def set_multimedia_content(self, content):
        """Set multimedia content from dict"""
        self.multimedia_content = json.dumps(content)
    
    def update_engagement_metrics(self, user_id, metrics):
        """Update engagement metrics with user interaction data"""
        current_metrics = self.get_engagement_metrics()
        if str(user_id) not in current_metrics:
            current_metrics[str(user_id)] = []
        
        current_metrics[str(user_id)].append({
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics
        })
        
        self.engagement_metrics = json.dumps(current_metrics)
    
    def get_engagement_metrics(self):
        """Get parsed engagement metrics"""
        if self.engagement_metrics:
            return json.loads(self.engagement_metrics)
        return {}
    
    def adapt_for_user(self, user_performance, user_preferences):
        """Adapt lesson content based on user performance and preferences"""
        adaptation = self.get_adaptation_data()
        
        # Adjust difficulty based on performance
        if user_performance < 0.6:  # If user struggling
            adaptation['difficulty_adjustment'] = -1
            adaptation['extra_hints'] = True
            adaptation['slower_pace'] = True
        elif user_performance > 0.9:  # If user excelling
            adaptation['difficulty_adjustment'] = 1
            adaptation['bonus_challenges'] = True
            adaptation['faster_pace'] = True
        
        # Adapt to preferences
        if user_preferences.get('visual_learner'):
            adaptation['visual_emphasis'] = True
        if user_preferences.get('auditory_learner'):
            adaptation['audio_emphasis'] = True
        if user_preferences.get('kinesthetic_learner'):
            adaptation['interactive_emphasis'] = True
        
        self.adaptation_data = json.dumps(adaptation)
        return adaptation
    
    def get_adaptation_data(self):
        """Get parsed adaptation data"""
        if self.adaptation_data:
            return json.loads(self.adaptation_data)
        return {}
    
    def is_prerequisite_met(self, user_completed_lessons):
        """Check if user has completed prerequisite lessons"""
        prerequisites = json.loads(self.prerequisite_lessons) if self.prerequisite_lessons else []
        return all(prereq_id in user_completed_lessons for prereq_id in prerequisites)
    
    def get_child_friendly_description(self):
        """Get a child-friendly description of the lesson"""
        descriptions = {
            'math': f"🧮 Let's play with numbers and solve fun puzzles!",
            'science': f"🔬 Time to discover amazing things about our world!",
            'language': f"📚 Let's learn new words and tell wonderful stories!",
            'art': f"🎨 Get ready to create beautiful masterpieces!",
            'music': f"🎵 Let's make beautiful sounds and rhythms!",
            'history': f"🏰 Journey back in time to meet amazing people!",
            'geography': f"🌍 Explore incredible places around the world!"
        }
        return descriptions.get(self.subject.lower(), f"🌟 Get ready for an awesome adventure in {self.subject}!")
    
    @staticmethod
    def create_sample_lessons():
        """Create sample lessons for development"""
        sample_lessons = [
            {
                'title': 'Magical Number Adventures',
                'subject': 'Math',
                'age_group': '4-6',
                'content': 'Join Sparkle the Dragon as we count magical crystals and solve number puzzles!',
                'interactive_elements': json.dumps([
                    {
                        'type': 'counting_game',
                        'description': 'Count the magical crystals',
                        'min_count': 1,
                        'max_count': 10
                    },
                    {
                        'type': 'shape_matching',
                        'description': 'Match shapes to help Sparkle',
                        'shapes': ['circle', 'square', 'triangle']
                    }
                ]),
                'rewards': json.dumps({
                    'pet_happiness': 10,
                    'pet_food': 2,
                    'accessories': ['magic_hat']
                }),
                'learning_objectives': json.dumps([
                    'Count from 1 to 10',
                    'Recognize basic shapes',
                    'Understand number sequence'
                ]),
                'emotional_tone': 'happy',
                'multimedia_content': json.dumps({
                    'background_music': 'gentle_adventure.mp3',
                    'character_voices': 'sparkle_dragon.mp3',
                    'animations': ['counting_sparkles', 'shape_dance']
                })
            },
            {
                'title': 'Rainbow Science Lab',
                'subject': 'Science',
                'age_group': '7-9',
                'content': 'Discover the magic of colors with Professor Whiskers the Cat!',
                'interactive_elements': json.dumps([
                    {
                        'type': 'color_mixing',
                        'description': 'Mix colors to create new ones',
                        'primary_colors': ['red', 'blue', 'yellow']
                    },
                    {
                        'type': 'rainbow_creator',
                        'description': 'Create your own rainbow',
                        'tools': ['prism', 'water', 'sunlight']
                    }
                ]),
                'rewards': json.dumps({
                    'pet_happiness': 15,
                    'pet_food': 3,
                    'accessories': ['scientist_goggles', 'lab_coat']
                }),
                'learning_objectives': json.dumps([
                    'Understand primary and secondary colors',
                    'Learn about light and prisms',
                    'Conduct simple experiments'
                ]),
                'emotional_tone': 'curious',
                'multimedia_content': json.dumps({
                    'background_music': 'discovery_theme.mp3',
                    'character_voices': 'professor_whiskers.mp3',
                    'animations': ['color_explosion', 'rainbow_formation']
                })
            }
        ]
        
        return sample_lessons


class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    
    # Progress tracking
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    progress_percentage = db.Column(db.Float, default=0.0)
    
    # Performance metrics
    attempts = db.Column(db.Integer, default=1)
    best_score = db.Column(db.Float, default=0.0)
    current_score = db.Column(db.Float, default=0.0)
    time_spent = db.Column(db.Integer, default=0)  # seconds
    
    # Engagement data for AI
    interaction_data = db.Column(db.Text)  # JSON for detailed interactions
    struggle_points = db.Column(db.Text)  # JSON for areas where user struggled
    success_patterns = db.Column(db.Text)  # JSON for successful interaction patterns
    
    # Emotional state during lesson
    emotional_state = db.Column(db.String(50))  # happy, frustrated, curious, bored
    mood_changes = db.Column(db.Text)  # JSON for mood tracking throughout lesson
    
    def __init__(self, user_id, lesson_id):
        self.user_id = user_id
        self.lesson_id = lesson_id
    
    def to_dict(self):
        """Convert progress to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'lesson_id': self.lesson_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_completed': self.is_completed,
            'progress_percentage': self.progress_percentage,
            'attempts': self.attempts,
            'best_score': self.best_score,
            'current_score': self.current_score,
            'time_spent': self.time_spent,
            'interaction_data': json.loads(self.interaction_data) if self.interaction_data else {},
            'struggle_points': json.loads(self.struggle_points) if self.struggle_points else [],
            'success_patterns': json.loads(self.success_patterns) if self.success_patterns else [],
            'emotional_state': self.emotional_state,
            'mood_changes': json.loads(self.mood_changes) if self.mood_changes else []
        }
    
    def update_progress(self, percentage, score=None, emotional_state=None):
        """Update progress with new data"""
        self.progress_percentage = min(100.0, percentage)
        
        if score is not None:
            self.current_score = score
            self.best_score = max(self.best_score, score)
        
        if emotional_state:
            self.emotional_state = emotional_state
        
        if self.progress_percentage >= 100.0:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
    
    def add_interaction_data(self, interaction_type, data):
        """Add interaction data for AI learning"""
        current_data = json.loads(self.interaction_data) if self.interaction_data else {}
        
        if interaction_type not in current_data:
            current_data[interaction_type] = []
        
        current_data[interaction_type].append({
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        })
        
        self.interaction_data = json.dumps(current_data)
    
    def add_struggle_point(self, concept, difficulty_level):
        """Record where user struggled for AI adaptation"""
        struggles = json.loads(self.struggle_points) if self.struggle_points else []
        struggles.append({
            'concept': concept,
            'difficulty_level': difficulty_level,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.struggle_points = json.dumps(struggles)
    
    def add_success_pattern(self, pattern_type, details):
        """Record successful learning patterns"""
        patterns = json.loads(self.success_patterns) if self.success_patterns else []
        patterns.append({
            'pattern_type': pattern_type,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.success_patterns = json.dumps(patterns)
    
    def track_mood_change(self, new_mood, context):
        """Track mood changes during lesson"""
        mood_changes = json.loads(self.mood_changes) if self.mood_changes else []
        mood_changes.append({
            'mood': new_mood,
            'context': context,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.mood_changes = json.dumps(mood_changes)


class LessonFeedback(db.Model):
    __tablename__ = 'lesson_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    
    # Child-friendly feedback
    fun_rating = db.Column(db.Integer)  # 1-5 stars
    difficulty_rating = db.Column(db.Integer)  # 1-5 (too easy to too hard)
    emoji_feedback = db.Column(db.String(50))  # emoji representing feeling
    
    # Detailed feedback
    favorite_part = db.Column(db.Text)
    suggestions = db.Column(db.Text)
    would_recommend = db.Column(db.Boolean)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id, lesson_id, **kwargs):
        self.user_id = user_id
        self.lesson_id = lesson_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'lesson_id': self.lesson_id,
            'fun_rating': self.fun_rating,
            'difficulty_rating': self.difficulty_rating,
            'emoji_feedback': self.emoji_feedback,
            'favorite_part': self.favorite_part,
            'suggestions': self.suggestions,
            'would_recommend': self.would_recommend,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }