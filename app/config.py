import os
from datetime import timedelta

class Config:
    # Basic Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'eduhope-magical-learning-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///eduhope.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'app/static/uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav'}
    
    # AI Model Configuration
    GPT2_MODEL_PATH = 'data/models/gpt2_edu'
    SENTIMENT_MODEL_PATH = 'cardiffnlp/twitter-roberta-base-sentiment-latest'
    
    # Real-time Learning Configuration
    LEARNING_ANALYTICS_ENABLED = True
    ADAPTIVE_LEARNING_ENABLED = True
    REAL_TIME_FEEDBACK = True
    
    # Pet System Configuration
    PET_TYPES = [
        'Dragon', 'Unicorn', 'Phoenix', 'Griffin', 'Pegasus', 'Fairy', 'Robot', 'Alien',
        'Mermaid', 'Wizard Cat', 'Rainbow Wolf', 'Crystal Fox', 'Star Bear', 'Moon Rabbit',
        'Fire Tiger', 'Ice Penguin', 'Forest Deer', 'Ocean Dolphin', 'Sky Eagle', 'Magic Turtle',
        'Cosmic Owl', 'Dream Horse', 'Thunder Lion', 'Flower Butterfly', 'Space Monkey'
    ]
    
    # Gamification Settings
    BASE_XP_REWARD = 10
    ACHIEVEMENT_MULTIPLIER = 2
    DAILY_LOGIN_BONUS = 5
    STREAK_MULTIPLIER = 1.5
    
    # Emotional Support Configuration
    MOOD_TRACKING_ENABLED = True
    AI_COMPANION_ENABLED = True
    CRISIS_KEYWORDS = ['sad', 'lonely', 'scared', 'angry', 'hurt', 'worried', 'afraid']
    
    # Content Moderation
    PROFANITY_FILTER_ENABLED = True
    CONTENT_SAFETY_ENABLED = True
    
    # Multilingual Support
    SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'de', 'hi', 'ar', 'zh', 'ja', 'pt', 'ru']
    DEFAULT_LANGUAGE = 'en'
    
    # Performance Settings
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CACHE_TYPE = 'simple'  # Use 'redis' in production
    CACHE_DEFAULT_TIMEOUT = 300
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}