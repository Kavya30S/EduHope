from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Achievement(db.Model):
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # learning, pet_care, social, emotional, creative
    
    # Visual elements
    icon = db.Column(db.String(100))  # emoji or image path
    color = db.Column(db.String(7), default='#FFD700')  # hex color
    animation = db.Column(db.String(100))  # animation name
    
    # Requirements
    requirements = db.Column(db.Text)  # JSON string with requirements
    points_required = db.Column(db.Integer, default=0)
    lessons_required = db.Column(db.Integer, default=0)
    pet_care_required = db.Column(db.Integer, default=0)
    social_interactions_required = db.Column(db.Integer, default=0)
    
    # Rewards
    rewards = db.Column(db.Text)  # JSON string with rewards
    pet_rewards = db.Column(db.Text)  # JSON string with pet-specific rewards
    
    # Metadata
    difficulty = db.Column(db.String(20), default='easy')  # easy, medium, hard, legendary
    is_secret = db.Column(db.Boolean, default=False)  # hidden achievements
    age_group = db.Column(db.String(50))  # age group this achievement is for
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user_achievements = db.relationship('UserAchievement', backref='achievement', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name, description, category, **kwargs):
        self.name = name
        self.description = description
        self.category = category
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert achievement to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'icon': self.icon,
            'color': self.color,
            'animation': self.animation,
            'requirements': json.loads(self.requirements) if self.requirements else {},
            'points_required': self.points_required,
            'lessons_required': self.lessons_required,
            'pet_care_required': self.pet_care_required,
            'social_interactions_required': self.social_interactions_required,
            'rewards': json.loads(self.rewards) if self.rewards else {},
            'pet_rewards': json.loads(self.pet_rewards) if self.pet_rewards else {},
            'difficulty': self.difficulty,
            'is_secret': self.is_secret,
            'age_group': self.age_group,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_requirements(self):
        """Get parsed requirements"""
        if self.requirements:
            return json.loads(self.requirements)
        return {}
    
    def set_requirements(self, requirements):
        """Set requirements from dict"""
        self.requirements = json.dumps(requirements)
    
    def get_rewards(self):
        """Get parsed rewards"""
        if self.rewards:
            return json.loads(self.rewards)
        return {}
    
    def set_rewards(self, rewards):
        """Set rewards from dict"""
        self.rewards = json.dumps(rewards)
    
    def get_pet_rewards(self):
        """Get parsed pet rewards"""
        if self.pet_rewards:
            return json.loads(self.pet_rewards)
        return {}
    
    def set_pet_rewards(self, rewards):
        """Set pet rewards from dict"""
        self.pet_rewards = json.dumps(rewards)
    
    def check_requirements(self, user_stats):
        """Check if user meets requirements for this achievement"""
        requirements = self.get_requirements()
        
        # Check basic requirements
        if self.points_required > 0 and user_stats.get('total_points', 0) < self.points_required:
            return False
        
        if self.lessons_required > 0 and user_stats.get('completed_lessons', 0) < self.lessons_required:
            return False
        
        if self.pet_care_required > 0 and user_stats.get('pet_care_actions', 0) < self.pet_care_required:
            return False
        
        if self.social_interactions_required > 0 and user_stats.get('social_interactions', 0) < self.social_interactions_required:
            return False
        
        # Check custom requirements
        for req_type, req_value in requirements.items():
            if req_type == 'consecutive_days':
                if user_stats.get('consecutive_days', 0) < req_value:
                    return False
            elif req_type == 'perfect_scores':
                if user_stats.get('perfect_scores', 0) < req_value:
                    return False
            elif req_type == 'subjects_mastered':
                if len(user_stats.get('mastered_subjects', [])) < req_value:
                    return False
            elif req_type == 'pet_happiness':
                if user_stats.get('pet_happiness', 0) < req_value:
                    return False
            elif req_type == 'stories_created':
                if user_stats.get('stories_created', 0) < req_value:
                    return False
            elif req_type == 'friends_helped':
                if user_stats.get('friends_helped', 0) < req_value:
                    return False
        
        return True
    
    def get_child_friendly_description(self):
        """Get a child-friendly description with emojis"""
        emoji_descriptions = {
            'learning': f"🎓 {self.description}",
            'pet_care': f"🐾 {self.description}",
            'social': f"👫 {self.description}",
            'emotional': f"💖 {self.description}",
            'creative': f"🎨 {self.description}"
        }
        return emoji_descriptions.get(self.category, f"⭐ {self.description}")
    
    @staticmethod
    def create_default_achievements():
        """Create default achievements for the system"""
        achievements = [
            # Learning Achievements
            {
                'name': 'First Steps',
                'description': 'Complete your very first lesson! 🎉',
                'category': 'learning',
                'icon': '🎓',
                'color': '#4CAF50',
                'animation': 'bounce',
                'lessons_required': 1,
                'rewards': json.dumps({
                    'points': 50,
                    'title': 'Young Scholar',
                    'badge': 'first_lesson'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 20,
                    'food': 5,
                    'accessories': ['graduation_cap']
                }),
                'difficulty': 'easy',
                'age_group': 'all'
            },
            {
                'name': 'Knowledge Seeker',
                'description': 'Complete 10 lessons and become a true knowledge seeker! 📚',
                'category': 'learning',
                'icon': '📚',
                'color': '#2196F3',
                'animation': 'pulse',
                'lessons_required': 10,
                'rewards': json.dumps({
                    'points': 200,
                    'title': 'Knowledge Seeker',
                    'badge': 'knowledge_seeker'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 50,
                    'food': 15,
                    'accessories': ['scholar_robe', 'magic_book']
                }),
                'difficulty': 'medium',
                'age_group': 'all'
            },
            {
                'name': 'Master of All',
                'description': 'Master 3 different subjects! You\'re amazing! 🌟',
                'category': 'learning',
                'icon': '🌟',
                'color': '#FFD700',
                'animation': 'sparkle',
                'requirements': json.dumps({
                    'subjects_mastered': 3
                }),
                'rewards': json.dumps({
                    'points': 500,
                    'title': 'Master Scholar',
                    'badge': 'master_scholar'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 100,
                    'food': 30,
                    'accessories': ['crown_of_wisdom', 'rainbow_cape']
                }),
                'difficulty': 'hard',
                'age_group': 'all'
            },
            
            # Pet Care Achievements
            {
                'name': 'Pet Lover',
                'description': 'Take care of your pet 5 times! They love you! 💕',
                'category': 'pet_care',
                'icon': '💕',
                'color': '#E91E63',
                'animation': 'heartbeat',
                'pet_care_required': 5,
                'rewards': json.dumps({
                    'points': 100,
                    'title': 'Pet Lover',
                    'badge': 'pet_lover'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 30,
                    'food': 10,
                    'accessories': ['heart_collar']
                }),
                'difficulty': 'easy',
                'age_group': 'all'
            },
            {
                'name': 'Pet Whisperer',
                'description': 'Keep your pet super happy for 7 days! 🌈',
                'category': 'pet_care',
                'icon': '🌈',
                'color': '#9C27B0',
                'animation': 'rainbow',
                'requirements': json.dumps({
                    'pet_happiness': 95,
                    'consecutive_days': 7
                }),
                'rewards': json.dumps({
                    'points': 300,
                    'title': 'Pet Whisperer',
                    'badge': 'pet_whisperer'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 50,
                    'food': 20,
                    'accessories': ['rainbow_wings', 'joy_halo']
                }),
                'difficulty': 'medium',
                'age_group': 'all'
            },
            
            # Social Achievements
            {
                'name': 'Friendly Helper',
                'description': 'Help 3 friends with their lessons! You\'re so kind! 🤗',
                'category': 'social',
                'icon': '🤗',
                'color': '#FF9800',
                'animation': 'wiggle',
                'requirements': json.dumps({
                    'friends_helped': 3
                }),
                'rewards': json.dumps({
                    'points': 150,
                    'title': 'Friendly Helper',
                    'badge': 'friendly_helper'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 40,
                    'food': 12,
                    'accessories': ['helper_badge']
                }),
                'difficulty': 'medium',
                'age_group': 'all'
            },
            
            # Creative Achievements
            {
                'name': 'Story Teller',
                'description': 'Create your first amazing story! 📖',
                'category': 'creative',
                'icon': '📖',
                'color': '#607D8B',
                'animation': 'fadeIn',
                'requirements': json.dumps({
                    'stories_created': 1
                }),
                'rewards': json.dumps({
                    'points': 100,
                    'title': 'Story Teller',
                    'badge': 'story_teller'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 35,
                    'food': 10,
                    'accessories': ['storyteller_hat']
                }),
                'difficulty': 'easy',
                'age_group': 'all'
            },
            {
                'name': 'Creative Genius',
                'description': 'Create 10 wonderful stories! You\'re so creative! 🎨',
                'category': 'creative',
                'icon': '🎨',
                'color': '#795548',
                'animation': 'spin',
                'requirements': json.dumps({
                    'stories_created': 10
                }),
                'rewards': json.dumps({
                    'points': 400,
                    'title': 'Creative Genius',
                    'badge': 'creative_genius'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 80,
                    'food': 25,
                    'accessories': ['artist_palette', 'inspiration_crown']
                }),
                'difficulty': 'hard',
                'age_group': 'all'
            },
            
            # Emotional Achievements
            {
                'name': 'Happy Learner',
                'description': 'Stay happy while learning for 5 days! 😊',
                'category': 'emotional',
                'icon': '😊',
                'color': '#FFEB3B',
                'animation': 'bounce',
                'requirements': json.dumps({
                    'consecutive_happy_days': 5
                }),
                'rewards': json.dumps({
                    'points': 200,
                    'title': 'Happy Learner',
                    'badge': 'happy_learner'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 60,
                    'food': 15,
                    'accessories': ['smile_badge', 'sunshine_aura']
                }),
                'difficulty': 'medium',
                'age_group': 'all'
            },
            {
                'name': 'Brave Explorer',
                'description': 'Try 5 difficult lessons without giving up! So brave! 🦁',
                'category': 'emotional',
                'icon': '🦁',
                'color': '#FF5722',
                'animation': 'roar',
                'requirements': json.dumps({
                    'difficult_lessons_attempted': 5
                }),
                'rewards': json.dumps({
                    'points': 250,
                    'title': 'Brave Explorer',
                    'badge': 'brave_explorer'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 70,
                    'food': 20,
                    'accessories': ['courage_medal', 'explorer_hat']
                }),
                'difficulty': 'medium',
                'age_group': 'all'
            },
            
            # Secret Achievements
            {
                'name': 'Night Owl',
                'description': 'Complete a lesson past bedtime! Shh... it\'s our secret! 🦉',
                'category': 'learning',
                'icon': '🦉',
                'color': '#3F51B5',
                'animation': 'mysterious',
                'requirements': json.dumps({
                    'night_lessons': 1
                }),
                'rewards': json.dumps({
                    'points': 100,
                    'title': 'Night Owl',
                    'badge': 'night_owl'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 25,
                    'food': 8,
                    'accessories': ['moon_hat', 'star_cape']
                }),
                'difficulty': 'easy',
                'is_secret': True,
                'age_group': 'all'
            },
            {
                'name': 'Speed Demon',
                'description': 'Complete a lesson in under 2 minutes! Lightning fast! ⚡',
                'category': 'learning',
                'icon': '⚡',
                'color': '#FFC107',
                'animation': 'lightning',
                'requirements': json.dumps({
                    'fastest_lesson_time': 120  # 2 minutes in seconds
                }),
                'rewards': json.dumps({
                    'points': 150,
                    'title': 'Speed Demon',
                    'badge': 'speed_demon'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 40,
                    'food': 12,
                    'accessories': ['lightning_bolt', 'speed_shoes']
                }),
                'difficulty': 'medium',
                'is_secret': True,
                'age_group': 'all'
            },
            
            # Special Achievements
            {
                'name': 'Perfect Week',
                'description': 'Get perfect scores for 7 days straight! Absolutely amazing! 🏆',
                'category': 'learning',
                'icon': '🏆',
                'color': '#FFD700',
                'animation': 'trophy_shine',
                'requirements': json.dumps({
                    'perfect_scores': 7,
                    'consecutive_days': 7
                }),
                'rewards': json.dumps({
                    'points': 1000,
                    'title': 'Perfection Master',
                    'badge': 'perfect_week'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 100,
                    'food': 50,
                    'accessories': ['golden_crown', 'victory_cape', 'perfect_medal']
                }),
                'difficulty': 'legendary',
                'age_group': 'all'
            },
            {
                'name': 'Rainbow Collector',
                'description': 'Collect all pet accessories! You\'re a true collector! 🌈',
                'category': 'pet_care',
                'icon': '🌈',
                'color': '#E91E63',
                'animation': 'rainbow_spiral',
                'requirements': json.dumps({
                    'accessories_collected': 50
                }),
                'rewards': json.dumps({
                    'points': 800,
                    'title': 'Rainbow Collector',
                    'badge': 'rainbow_collector'
                }),
                'pet_rewards': json.dumps({
                    'happiness': 100,
                    'food': 40,
                    'accessories': ['rainbow_everything']
                }),
                'difficulty': 'legendary',
                'age_group': 'all'
            }
        ]
        
        return achievements


class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    
    # Achievement data
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress_when_earned = db.Column(db.Text)  # JSON snapshot of user progress
    celebration_viewed = db.Column(db.Boolean, default=False)
    
    # Social sharing
    shared_with_friends = db.Column(db.Boolean, default=False)
    sharing_message = db.Column(db.Text)
    
    def __init__(self, user_id, achievement_id):
        self.user_id = user_id
        self.achievement_id = achievement_id
    
    def to_dict(self):
        """Convert user achievement to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
            'progress_when_earned': json.loads(self.progress_when_earned) if self.progress_when_earned else {},
            'celebration_viewed': self.celebration_viewed,
            'shared_with_friends': self.shared_with_friends,
            'sharing_message': self.sharing_message
        }
    
    def set_progress_snapshot(self, progress_data):
        """Set progress snapshot when achievement was earned"""
        self.progress_when_earned = json.dumps(progress_data)
    
    def get_progress_snapshot(self):
        """Get progress snapshot"""
        if self.progress_when_earned:
            return json.loads(self.progress_when_earned)
        return {}
    
    def mark_celebration_viewed(self):
        """Mark that user has viewed the achievement celebration"""
        self.celebration_viewed = True
    
    def share_achievement(self, message=None):
        """Share achievement with friends"""
        self.shared_with_friends = True
        if message:
            self.sharing_message = message


class AchievementCategory(db.Model):
    __tablename__ = 'achievement_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100))
    color = db.Column(db.String(7))
    sort_order = db.Column(db.Integer, default=0)
    
    def __init__(self, name, display_name, **kwargs):
        self.name = name
        self.display_name = display_name
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'sort_order': self.sort_order
        }
    
    @staticmethod
    def create_default_categories():
        """Create default achievement categories"""
        categories = [
            {
                'name': 'learning',
                'display_name': 'Learning Explorer',
                'description': 'Achievements for completing lessons and mastering subjects',
                'icon': '🎓',
                'color': '#4CAF50',
                'sort_order': 1
            },
            {
                'name': 'pet_care',
                'display_name': 'Pet Guardian',
                'description': 'Achievements for taking amazing care of your virtual pet',
                'icon': '🐾',
                'color': '#E91E63',
                'sort_order': 2
            },
            {
                'name': 'social',
                'display_name': 'Friendship Champion',
                'description': 'Achievements for helping friends and being social',
                'icon': '👫',
                'color': '#FF9800',
                'sort_order': 3
            },
            {
                'name': 'creative',
                'display_name': 'Creative Artist',
                'description': 'Achievements for creating stories and being creative',
                'icon': '🎨',
                'color': '#9C27B0',
                'sort_order': 4
            },
            {
                'name': 'emotional',
                'display_name': 'Emotional Warrior',
                'description': 'Achievements for emotional growth and resilience',
                'icon': '💖',
                'color': '#F44336',
                'sort_order': 5
            }
        ]
        
        return categories