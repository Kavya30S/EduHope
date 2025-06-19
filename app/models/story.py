from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Story(db.Model):
    __tablename__ = 'stories'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Story properties
    genre = db.Column(db.String(50), default='Adventure')
    is_public = db.Column(db.Boolean, default=True)
    is_collaborative = db.Column(db.Boolean, default=False)
    is_completed = db.Column(db.Boolean, default=False)
    
    # Engagement metrics
    likes = db.Column(db.Integer, default=0)
    reads = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Content moderation
    is_moderated = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    
    # Relationships
    collaborators = db.relationship('StoryCollaborator', backref='story', lazy='dynamic')
    
    def __repr__(self):
        return f'<Story {self.title}>'
    
    def add_collaborator(self, user_id):
        """Add a collaborator to the story"""
        if not self.collaborators.filter_by(user_id=user_id).first():
            collaborator = StoryCollaborator(story_id=self.id, user_id=user_id)
            db.session.add(collaborator)
            return True
        return False
    
    def get_word_count(self):
        """Get word count of the story"""
        return len(self.content.split())
    
    def get_reading_time(self):
        """Estimate reading time in minutes"""
        words = self.get_word_count()
        return max(1, words // 200)  # Average reading speed
    
    def to_dict(self):
        """Convert story to dictionary for JSON responses"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author_id': self.author_id,
            'author_name': self.author.username if self.author else 'Unknown',
            'genre': self.genre,
            'is_public': self.is_public,
            'is_collaborative': self.is_collaborative,
            'is_completed': self.is_completed,
            'likes': self.likes,
            'reads': self.reads,
            'shares': self.shares,
            'word_count': self.get_word_count(),
            'reading_time': self.get_reading_time(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_featured': self.is_featured
        }

class StoryCollaborator(db.Model):
    __tablename__ = 'story_collaborators'
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contribution_count = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StoryCollaborator {self.user_id} on {self.story_id}>'