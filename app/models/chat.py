"""
Chat Model for handling AI conversations and emotional support
"""
from app import db
from datetime import datetime, timedelta
import json
from enum import Enum

class ChatType(Enum):
    GENERAL = "general"
    EMOTIONAL_SUPPORT = "emotional_support"
    EDUCATIONAL = "educational"
    PET_COMPANION = "pet_companion"
    STORYTELLING = "storytelling"

class EmotionLevel(Enum):
    VERY_HAPPY = "very_happy"
    HAPPY = "happy"
    NEUTRAL = "neutral"
    SAD = "sad"
    VERY_SAD = "very_sad"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    CONFUSED = "confused"

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_name = db.Column(db.String(100))
    chat_type = db.Column(db.Enum(ChatType), default=ChatType.GENERAL)
    initial_emotion = db.Column(db.Enum(EmotionLevel), default=EmotionLevel.NEUTRAL)
    current_emotion = db.Column(db.Enum(EmotionLevel), default=EmotionLevel.NEUTRAL)
    session_metadata = db.Column(db.Text)  # JSON for session-specific data
    is_active = db.Column(db.Boolean, default=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    total_messages = db.Column(db.Integer, default=0)
    
    # Relationships
    user = db.relationship('User', backref='chat_sessions')
    messages = db.relationship('ChatMessage', backref='session', cascade='all, delete-orphan')

    def __init__(self, user_id, **kwargs):
        self.user_id = user_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_metadata(self):
        """Parse and return session metadata as dictionary"""
        if self.session_metadata:
            try:
                return json.loads(self.session_metadata)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_metadata(self, data):
        """Set session metadata as JSON string"""
        self.session_metadata = json.dumps(data)

    def end_session(self):
        """End the chat session"""
        self.is_active = False
        self.ended_at = datetime.utcnow()
        db.session.commit()

    def get_duration(self):
        """Get session duration in minutes"""
        end_time = self.ended_at or datetime.utcnow()
        duration = end_time - self.started_at
        return duration.total_seconds() / 60

    def update_emotion(self, new_emotion):
        """Update current emotion level"""
        self.current_emotion = new_emotion
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_name': self.session_name,
            'chat_type': self.chat_type.value if self.chat_type else None,
            'initial_emotion': self.initial_emotion.value if self.initial_emotion else None,
            'current_emotion': self.current_emotion.value if self.current_emotion else None,
            'metadata': self.get_metadata(),
            'is_active': self.is_active,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'total_messages': self.total_messages,
            'duration_minutes': self.get_duration()
        }

    def __repr__(self):
        return f'<ChatSession {self.id} - {self.user_id}>'


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_type = db.Column(db.String(20), default='text')  # 'text', 'emotion', 'image', 'audio'
    content = db.Column(db.Text, nullable=False)
    is_from_user = db.Column(db.Boolean, default=True)
    ai_response_type = db.Column(db.String(50))  # 'supportive', 'educational', 'playful', 'encouraging'
    emotion_detected = db.Column(db.Enum(EmotionLevel))
    sentiment_score = db.Column(db.Float)  # -1.0 to 1.0
    confidence_score = db.Column(db.Float)  # 0.0 to 1.0
    message_metadata = db.Column(db.Text)  # JSON for message-specific data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='chat_messages')

    def __init__(self, session_id, user_id, content, **kwargs):
        self.session_id = session_id
        self.user_id = user_id
        self.content = content
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_metadata(self):
        """Parse and return message metadata as dictionary"""
        if self.message_metadata:
            try:
                return json.loads(self.message_metadata)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_metadata(self, data):
        """Set message metadata as JSON string"""
        self.message_metadata = json.dumps(data)

    def analyze_sentiment(self):
        """Analyze sentiment of the message (placeholder for real implementation)"""
        # This would integrate with sentiment analysis service
        positive_words = ['happy', 'joy', 'love', 'excited', 'good', 'great', 'amazing', 'wonderful']
        negative_words = ['sad', 'angry', 'hate', 'bad', 'terrible', 'awful', 'upset', 'worried']
        
        content_lower = self.content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            self.sentiment_score = 0.5 + (positive_count - negative_count) * 0.1
        elif negative_count > positive_count:
            self.sentiment_score = -0.5 - (negative_count - positive_count) * 0.1
        else:
            self.sentiment_score = 0.0
            
        self.sentiment_score = max(-1.0, min(1.0, self.sentiment_score))
        
        # Detect emotion based on keywords
        if any(word in content_lower for word in ['happy', 'joy', 'excited', 'great']):
            self.emotion_detected = EmotionLevel.HAPPY
        elif any(word in content_lower for word in ['sad', 'cry', 'upset']):
            self.emotion_detected = EmotionLevel.SAD
        elif any(word in content_lower for word in ['angry', 'mad', 'furious']):
            self.emotion_detected = EmotionLevel.ANGRY
        elif any(word in content_lower for word in ['worried', 'anxious', 'scared']):
            self.emotion_detected = EmotionLevel.ANXIOUS
        elif any(word in content_lower for word in ['confused', 'don\'t understand']):
            self.emotion_detected = EmotionLevel.CONFUSED

    def generate_ai_response(self, learning_context=None):
        """Generate AI response based on message content and context"""
        # This would integrate with the AI service
        responses = {
            EmotionLevel.SAD: [
                "I can see you're feeling sad. Would you like to talk about what's making you feel this way?",
                "It's okay to feel sad sometimes. Let's see if we can find something that might help you feel better.",
                "You're not alone in feeling this way. Would you like to play a fun game with your pet?"
            ],
            EmotionLevel.ANGRY: [
                "I notice you might be feeling angry. Let's take some deep breaths together.",
                "It's normal to feel angry sometimes. Would you like to tell me what's bothering you?",
                "When I feel angry, I like to count to ten. Would you like to try that with me?"
            ],
            EmotionLevel.ANXIOUS: [
                "I can sense you might be feeling worried. Remember, you're safe here with me.",
                "Let's try some calming exercises together. Take a deep breath in... and out...",
                "It's okay to feel anxious. Would you like to pet your virtual companion for comfort?"
            ],
            EmotionLevel.HAPPY: [
                "I'm so happy to see you're feeling good! What made you happy today?",
                "Your happiness is contagious! Would you like to share this joy with your pet?",
                "That's wonderful! Let's celebrate by unlocking something special for your pet!"
            ],
            EmotionLevel.CONFUSED: [
                "I can help you understand! What would you like me to explain?",
                "It's okay to be confused - that's how we learn! Let's figure this out together.",
                "Questions are great! They help us learn new things. What are you wondering about?"
            ]
        }
        
        default_responses = [
            "That's interesting! Tell me more about that.",
            "I'm here to listen and help. What would you like to talk about?",
            "You're doing great! Is there anything you'd like to learn about today?",
            "I love chatting with you! What's on your mind?"
        ]
        
        if self.emotion_detected and self.emotion_detected in responses:
            import random
            return random.choice(responses[self.emotion_detected])
        else:
            import random
            return random.choice(default_responses)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'message_type': self.message_type,
            'content': self.content,
            'is_from_user': self.is_from_user,
            'ai_response_type': self.ai_response_type,
            'emotion_detected': self.emotion_detected.value if self.emotion_detected else None,
            'sentiment_score': self.sentiment_score,
            'confidence_score': self.confidence_score,
            'metadata': self.get_metadata(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def get_recent_messages(session_id, limit=20):
        """Get recent messages for a session"""
        return ChatMessage.query.filter_by(session_id=session_id)\
                               .order_by(ChatMessage.created_at.desc())\
                               .limit(limit).all()

    @staticmethod
    def get_user_emotion_history(user_id, days=7):
        """Get user's emotion history for analysis"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return ChatMessage.query.filter(
            ChatMessage.user_id == user_id,
            ChatMessage.emotion_detected.isnot(None),
            ChatMessage.created_at >= cutoff_date
        ).order_by(ChatMessage.created_at.desc()).all()

    def __repr__(self):
        return f'<ChatMessage {self.id} - Session:{self.session_id}>'