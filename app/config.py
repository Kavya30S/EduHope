import os

class Config:
    """Configuration settings for EduHope application."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key-for-kids')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'app/static/uploads'
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = 'redis://localhost:6379/0'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your-app-password')
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_SUPPORTED_LOCALES = ['en', 'es', 'fr', 'ar']
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    RATE_LIMIT_STORAGE_URL = 'redis://localhost:6379/0'
    RATE_LIMIT_DEFAULTS = ['200 per day', '50 per hour']
    
    # Child-friendly UI settings
    THEME_COLORS = {
        'primary': '#FF6B35',
        'secondary': '#FFB6C1',
        'accent': '#87CEEB',
        'highlight': '#FFD700'
    }
    
    # Pet system settings
    PET_TYPES = [
        'Dragon', 'Unicorn', 'Robot', 'Phoenix', 'Griffin',
        'Mermaid', 'Yeti', 'Pixie', 'Kraken', 'Sphinx'
    ]
    PET_ACCESSORY_CATEGORIES = ['Hat', 'Cape', 'Shoes', 'Necklace', 'Wings']
    
    # Dataset paths
    DATASET_PATHS = {
        'wikitext': 'data/datasets/wikitext',
        'folktales': 'data/datasets/folktales',
        'ck12': 'data/datasets/ck12',
        'wikipedia': 'data/datasets/wikipedia',
        'who': 'data/datasets/who',
        'tatoeba': 'data/datasets/tatoeba'
    }
    
    # AI model paths
    MODEL_PATHS = {
        'gpt2_edu': 'data/models/gpt2_edu'
    }
    
    # Email notification settings
    NOTIFICATION_SUBJECTS = {
        'login': 'EduHope: Child Login Notification',
        'progress': 'EduHope: Child Progress Update',
        'emotion': 'EduHope: Child Emotional Update'
    }
    
    def __init__(self):
        """Initialize configuration with environment variables."""
        self.validate_config()
    
    def validate_config(self):
        """Validate configuration settings."""
        required_env_vars = ['MAIL_USERNAME', 'MAIL_PASSWORD']
        for var in required_env_vars:
            if not os.environ.get(var):
                print(f"Warning: Environment variable {var} not set")
    
    def get_theme_color(self, key: str) -> str:
        """Get theme color by key."""
        return self.THEME_COLORS.get(key, '#FF6B35')
    
    def get_dataset_path(self, dataset: str) -> str:
        """Get dataset path by key."""
        return self.DATASET_PATHS.get(dataset, '')
    
    def get_model_path(self, model: str) -> str:
        """Get model path by key."""
        return self.MODEL_PATHS.get(model, '')
    
    def get_notification_subject(self, notification_type: str) -> str:
        """Get notification subject by type."""
        return self.NOTIFICATION_SUBJECTS.get(notification_type, 'EduHope Notification')