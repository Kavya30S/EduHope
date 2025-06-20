"""
Game Progress Model for tracking children's gameplay and learning progress
"""
from app import db
from datetime import datetime, timedelta
import json

class GameProgress(db.Model):
    __tablename__ = 'game_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)  # 'memory', 'math', 'language', 'creativity'
    level = db.Column(db.Integer, default=1)
    score = db.Column(db.Integer, default=0)
    highest_score = db.Column(db.Integer, default=0)
    time_spent = db.Column(db.Integer, default=0)  # in seconds
    attempts = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    streak_count = db.Column(db.Integer, default=0)
    last_played = db.Column(db.DateTime, default=datetime.utcnow)
    game_data = db.Column(db.Text)  # JSON string for specific game data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='game_progress')

    def __init__(self, user_id, game_type, **kwargs):
        self.user_id = user_id
        self.game_type = game_type
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def update_progress(self, score, time_spent, success=True):
        """Update game progress with new score and time"""
        self.attempts += 1
        self.time_spent += time_spent
        self.last_played = datetime.utcnow()
        
        if score > self.highest_score:
            self.highest_score = score
            
        if success:
            self.streak_count += 1
            # Level up logic based on streak and score
            if self.streak_count >= 3 and self.score >= self.level * 100:
                self.level += 1
                self.streak_count = 0  # Reset streak after leveling up
        else:
            self.streak_count = 0
            
        # Calculate success rate
        total_successful = self.attempts * self.success_rate + (1 if success else 0)
        self.success_rate = total_successful / self.attempts
        
        self.score = score
        self.updated_at = datetime.utcnow()

    def get_game_data(self):
        """Parse and return game data as dictionary"""
        if self.game_data:
            try:
                return json.loads(self.game_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_game_data(self, data):
        """Set game data as JSON string"""
        self.game_data = json.dumps(data)

    def is_ready_for_level_up(self):
        """Check if player is ready for next level"""
        return (self.streak_count >= 3 and 
                self.success_rate >= 0.7 and 
                self.score >= self.level * 100)

    def get_progress_percentage(self):
        """Get progress percentage for current level"""
        current_level_requirement = self.level * 100
        return min(100, (self.score / current_level_requirement) * 100)

    def get_playing_time_today(self):
        """Get total playing time for today"""
        today = datetime.utcnow().date()
        if self.last_played.date() == today:
            return self.time_spent
        return 0

    def can_play_today(self, max_daily_time=3600):  # 1 hour default
        """Check if user can still play today based on time limits"""
        return self.get_playing_time_today() < max_daily_time

    def get_achievements(self):
        """Get list of achievements based on progress"""
        achievements = []
        
        if self.level >= 5:
            achievements.append("Level Master")
        if self.highest_score >= 1000:
            achievements.append("High Scorer")
        if self.streak_count >= 10:
            achievements.append("Streak Champion")
        if self.success_rate >= 0.9:
            achievements.append("Accuracy Expert")
        if self.attempts >= 50:
            achievements.append("Persistent Player")
            
        return achievements

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'game_type': self.game_type,
            'level': self.level,
            'score': self.score,
            'highest_score': self.highest_score,
            'time_spent': self.time_spent,
            'attempts': self.attempts,
            'success_rate': round(self.success_rate, 2),
            'streak_count': self.streak_count,
            'last_played': self.last_played.isoformat() if self.last_played else None,
            'game_data': self.get_game_data(),
            'progress_percentage': self.get_progress_percentage(),
            'achievements': self.get_achievements(),
            'can_play_today': self.can_play_today(),
            'ready_for_level_up': self.is_ready_for_level_up()
        }

    @staticmethod
    def get_user_progress(user_id, game_type=None):
        """Get all progress for a user, optionally filtered by game type"""
        query = GameProgress.query.filter_by(user_id=user_id)
        if game_type:
            query = query.filter_by(game_type=game_type)
        return query.all()

    @staticmethod
    def get_or_create_progress(user_id, game_type):
        """Get existing progress or create new one"""
        progress = GameProgress.query.filter_by(
            user_id=user_id, 
            game_type=game_type
        ).first()
        
        if not progress:
            progress = GameProgress(user_id=user_id, game_type=game_type)
            db.session.add(progress)
            db.session.commit()
            
        return progress

    def __repr__(self):
        return f'<GameProgress {self.user_id}:{self.game_type} Level:{self.level}>'