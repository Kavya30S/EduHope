from datetime import datetime
from app import db
from sqlalchemy.orm import relationship
import json

class Story(db.Model):
    __tablename__ = 'stories'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    genre = db.Column(db.String(50), default='adventure')
    difficulty_level = db.Column(db.Integer, default=1)
    is_collaborative = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    
    # Creator info
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_stories")
    
    # Story statistics
    views_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    completion_rate = db.Column(db.Float, default=0.0)
    
    # AI-generated elements
    ai_suggestions = db.Column(db.Text)  # JSON string of AI suggestions
    moral_lesson = db.Column(db.String(500))
    age_appropriate = db.Column(db.Boolean, default=True)
    
    # Multimedia elements
    has_audio = db.Column(db.Boolean, default=False)
    has_images = db.Column(db.Boolean, default=False)
    background_music = db.Column(db.String(100))  # Music theme
    
    # Fantasy elements for children
    magical_elements = db.Column(db.Text)  # JSON string of magical elements
    character_pets = db.Column(db.Text)  # JSON string of pets in story
    adventure_level = db.Column(db.Integer, default=1)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    collaborations = relationship("StoryCollaboration", back_populates="story", cascade="all, delete-orphan")
    story_progress = relationship("StoryProgress", back_populates="story", cascade="all, delete-orphan")
    story_ratings = relationship("StoryRating", back_populates="story", cascade="all, delete-orphan")
    
    def __init__(self, title, content, creator_id, **kwargs):
        self.title = title
        self.content = content
        self.creator_id = creator_id
        
        # Process magical elements for children
        self.magical_elements = json.dumps(kwargs.get('magical_elements', [
            "Talking animals", "Magic spells", "Flying creatures", 
            "Enchanted forests", "Glowing crystals", "Fairy dust"
        ]))
        
        # Set other attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_magical_elements(self):
        """Get magical elements as a list"""
        try:
            return json.loads(self.magical_elements) if self.magical_elements else []
        except:
            return []
    
    def add_magical_element(self, element):
        """Add a magical element to the story"""
        elements = self.get_magical_elements()
        if element not in elements:
            elements.append(element)
            self.magical_elements = json.dumps(elements)
    
    def get_character_pets(self):
        """Get character pets as a list"""
        try:
            return json.loads(self.character_pets) if self.character_pets else []
        except:
            return []
    
    def add_character_pet(self, pet_name, pet_type):
        """Add a character pet to the story"""
        pets = self.get_character_pets()
        pets.append({"name": pet_name, "type": pet_type})
        self.character_pets = json.dumps(pets)
    
    def get_ai_suggestions(self):
        """Get AI suggestions as a dict"""
        try:
            return json.loads(self.ai_suggestions) if self.ai_suggestions else {}
        except:
            return {}
    
    def add_ai_suggestion(self, suggestion_type, suggestion):
        """Add an AI suggestion"""
        suggestions = self.get_ai_suggestions()
        if suggestion_type not in suggestions:
            suggestions[suggestion_type] = []
        suggestions[suggestion_type].append(suggestion)
        self.ai_suggestions = json.dumps(suggestions)
    
    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
        db.session.commit()
    
    def add_like(self):
        """Add a like to the story"""
        self.likes_count += 1
        db.session.commit()
    
    def get_difficulty_description(self):
        """Get human-readable difficulty level"""
        levels = {
            1: "Beginner - Easy words and simple sentences",
            2: "Elementary - Short paragraphs with pictures",
            3: "Intermediate - Longer stories with adventures",
            4: "Advanced - Complex plots and characters",
            5: "Expert - Rich vocabulary and deep themes"
        }
        return levels.get(self.difficulty_level, "Unknown")
    
    def is_suitable_for_age(self, age):
        """Check if story is suitable for given age"""
        if age <= 6:
            return self.difficulty_level <= 2
        elif age <= 9:
            return self.difficulty_level <= 3
        elif age <= 12:
            return self.difficulty_level <= 4
        else:
            return True
    
    def get_reading_time(self):
        """Estimate reading time in minutes"""
        words = len(self.content.split())
        # Assume average reading speed for children: 100-150 words per minute
        return max(1, round(words / 125))
    
    def to_dict(self):
        """Convert story to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'genre': self.genre,
            'difficulty_level': self.difficulty_level,
            'difficulty_description': self.get_difficulty_description(),
            'is_collaborative': self.is_collaborative,
            'is_published': self.is_published,
            'is_featured': self.is_featured,
            'creator_id': self.creator_id,
            'views_count': self.views_count,
            'likes_count': self.likes_count,
            'completion_rate': self.completion_rate,
            'moral_lesson': self.moral_lesson,
            'age_appropriate': self.age_appropriate,
            'has_audio': self.has_audio,
            'has_images': self.has_images,
            'background_music': self.background_music,
            'magical_elements': self.get_magical_elements(),
            'character_pets': self.get_character_pets(),
            'adventure_level': self.adventure_level,
            'reading_time': self.get_reading_time(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class StoryCollaboration(db.Model):
    __tablename__ = 'story_collaborations'
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contribution = db.Column(db.Text, nullable=False)
    contribution_type = db.Column(db.String(50), default='text')  # text, idea, character, plot
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    story = relationship("Story", back_populates="collaborations")
    user = relationship("User", foreign_keys=[user_id])

class StoryProgress(db.Model):
    __tablename__ = 'story_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)
    progress_percentage = db.Column(db.Float, default=0.0)
    last_position = db.Column(db.Integer, default=0)  # Character position in story
    is_completed = db.Column(db.Boolean, default=False)
    completion_time = db.Column(db.Integer)  # Time taken to complete in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    story = relationship("Story", back_populates="story_progress")

class StoryRating(db.Model):
    __tablename__ = 'story_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review = db.Column(db.Text)
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    story = relationship("Story", back_populates="story_ratings")
    
    def __init__(self, user_id, story_id, rating, review=None):
        self.user_id = user_id
        self.story_id = story_id
        self.rating = max(1, min(5, rating))  # Ensure rating is between 1-5
        self.review = review