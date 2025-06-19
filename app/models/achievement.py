from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Achievement(db.Model):
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    badge_icon = db.Column(db.String(50))  # Icon class or image path
    badge_color = db.Column(db.String(20), default='gold')
    points_reward = db.Column(db.Integer, default=100)
    category = db.Column(db.String(50))  # learning, pet_care, social, creativity
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_rare = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Achievement {self.name}>'
    
    def to_dict(self):
        """Convert achievement to dictionary for JSON responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'badge_icon': self.badge_icon,
            'badge_color': self.badge_color,
            'points_reward': self.points_reward,
            'category': self.category,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
            'is_rare': self.is_rare
        }

# Predefined achievements that users can earn
ACHIEVEMENT_DEFINITIONS = [
    {
        'name': 'First Steps',
        'description': 'Complete your first lesson!',
        'badge_icon': '🎯',
        'category': 'learning',
        'trigger': 'lessons_completed',
        'threshold': 1,
        'points': 50
    },
    {
        'name': 'Learning Enthusiast',
        'description': 'Complete 10 lessons!',
        'badge_icon': '📚',
        'category': 'learning',
        'trigger': 'lessons_completed',
        'threshold': 10,
        'points': 200
    },
    {
        'name': 'Pet Lover',
        'description': 'Feed your pet 10 times!',
        'badge_icon': '❤️',
        'category': 'pet_care',
        'trigger': 'pet_fed',
        'threshold': 10,
        'points': 100
    },
    {
        'name': 'Pet Master',
        'description': 'Raise your pet to level 5!',
        'badge_icon': '👑',
        'category': 'pet_care',
        'trigger': 'pet_level',
        'threshold': 5,
        'points': 300,
        'is_rare': True
    },
    {
        'name': 'Math Wizard',
        'description': 'Score 100% on 5 math lessons!',
        'badge_icon': '🧙‍♂️',
        'category': 'learning',
        'trigger': 'perfect_math_scores',
        'threshold': 5,
        'points': 250
    },
    {
        'name': 'Word Master',
        'description': 'Complete 10 language games!',
        'badge_icon': '📝',
        'category': 'learning',
        'trigger': 'language_games',
        'threshold': 10,
        'points': 200
    },
    {
        'name': 'Creative Soul',
        'description': 'Write 5 stories!',
        'badge_icon': '✨',
        'category': 'creativity',
        'trigger': 'stories_written',
        'threshold': 5,
        'points': 300
    },
    {
        'name': 'Social Butterfly',
        'description': 'Make 3 friends!',
        'badge_icon': '🦋',
        'category': 'social',
        'trigger': 'friends_made',
        'threshold': 3,
        'points': 150
    },
    {
        'name': 'Daily Dedication',
        'description': 'Login for 7 consecutive days!',
        'badge_icon': '🔥',
        'category': 'engagement',
        'trigger': 'streak_days',
        'threshold': 7,
        'points': 400
    },
    {
        'name': 'Point Collector',
        'description': 'Earn 1000 points!',
        'badge_icon': '💎',
        'category': 'engagement',
        'trigger': 'total_points',
        'threshold': 1000,
        'points': 500,
        'is_rare': True
    },
    {
        'name': 'Game Champion',
        'description': 'Complete the Math Maze 5 times!',
        'badge_icon': '🏆',
        'category': 'learning',
        'trigger': 'games_completed',
        'threshold': 5,
        'points': 200
    },
    {
        'name': 'Happy Pet',
        'description': 'Keep your pet happiness above 90 for a day!',
        'badge_icon': '😊',
        'category': 'pet_care',
        'trigger': 'pet_happiness_day',
        'threshold': 1,
        'points': 150
    },
    {
        'name': 'Explorer',
        'description': 'Try all different lesson subjects!',
        'badge_icon': '🗺️',
        'category': 'learning',
        'trigger': 'subjects_explored',
        'threshold': 5,
        'points': 300
    },
    {
        'name': 'Helper',
        'description': 'Help other children in collaborative activities!',
        'badge_icon': '🤝',
        'category': 'social',
        'trigger': 'helped_others',
        'threshold': 10,
        'points': 250
    },
    {
        'name': 'Night Owl',
        'description': 'Complete lessons in the evening!',
        'badge_icon': '🦉',
        'category': 'engagement',
        'trigger': 'evening_lessons',
        'threshold': 5,
        'points': 100
    }
]

def check_and_award_achievements(user, trigger_type, current_value):
    """Check if user has earned any new achievements"""
    new_achievements = []
    
    for achievement_def in ACHIEVEMENT_DEFINITIONS:
        if achievement_def['trigger'] == trigger_type:
            # Check if user already has this achievement
            existing = Achievement.query.filter_by(
                user_id=user.id,
                name=achievement_def['name']
            ).first()
            
            if not existing and current_value >= achievement_def['threshold']:
                # Award the achievement
                achievement = Achievement(
                    user_id=user.id,
                    name=achievement_def['name'],
                    description=achievement_def['description'],
                    badge_icon=achievement_def['badge_icon'],
                    category=achievement_def['category'],
                    points_reward=achievement_def['points'],
                    is_rare=achievement_def.get('is_rare', False)
                )
                
                db.session.add(achievement)
                user.points += achievement_def['points']
                new_achievements.append(achievement)
    
    return new_achievements