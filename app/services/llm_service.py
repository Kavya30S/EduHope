import os
import json
import requests
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import threading
import time

# Translation libraries
try:
    from googletrans import Translator as GoogleTranslator
    import translators as ts
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    logging.warning("Translation libraries not available. Translation features will be limited.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.google_translator = None
        self.supported_languages = {
            'en': {'name': 'English', 'flag': '🇺🇸', 'native': 'English'},
            'es': {'name': 'Spanish', 'flag': '🇪🇸', 'native': 'Español'},
            'fr': {'name': 'French', 'flag': '🇫🇷', 'native': 'Français'},
            'de': {'name': 'German', 'flag': '🇩🇪', 'native': 'Deutsch'},
            'hi': {'name': 'Hindi', 'flag': '🇮🇳', 'native': 'हिन्दी'},
            'zh': {'name': 'Chinese', 'flag': '🇨🇳', 'native': '中文'},
            'ja': {'name': 'Japanese', 'flag': '🇯🇵', 'native': '日本語'},
            'ko': {'name': 'Korean', 'flag': '🇰🇷', 'native': '한국어'},
            'ar': {'name': 'Arabic', 'flag': '🇸🇦', 'native': 'العربية'},
            'pt': {'name': 'Portuguese', 'flag': '🇵🇹', 'native': 'Português'},
            'ru': {'name': 'Russian', 'flag': '🇷🇺', 'native': 'Русский'},
            'it': {'name': 'Italian', 'flag': '🇮🇹', 'native': 'Italiano'},
            'tr': {'name': 'Turkish', 'flag': '🇹🇷', 'native': 'Türkçe'},
            'pl': {'name': 'Polish', 'flag': '🇵🇱', 'native': 'Polski'},
            'nl': {'name': 'Dutch', 'flag': '🇳🇱', 'native': 'Nederlands'}
        }
        
        self.user_preferences = {}
        self.translation_cache = {}
        self.offline_translations = {}
        self.initialize_translation_services()
        self.load_offline_translations()
        
    def initialize_translation_services(self):
        """Initialize translation services"""
        if not TRANSLATION_AVAILABLE:
            logger.warning("Translation libraries not available")
            return
            
        try:
            self.google_translator = GoogleTranslator()
            logger.info("Translation services initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing translation services: {e}")
            TRANSLATION_AVAILABLE = False
    
    def load_offline_translations(self):
        """Load offline translation d