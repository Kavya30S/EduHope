import requests
import json
import logging
from typing import Dict, List, Optional
from functools import lru_cache
import sqlite3
import os

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.base_url = "http://localhost:5000"  # LibreTranslate local server
        self.cache_db = "app/data/translation_cache.db"
        self.init_cache_db()
        
        # Kid-friendly language mapping
        self.language_pets = {
            'en': '🐰', 'es': '🦜', 'fr': '🐸', 'de': '🐻',
            'it': '🦊', 'pt': '🐨', 'ru': '🐺', 'zh': '🐼',
            'ja': '🐱', 'ko': '🐶', 'hi': '🐘', 'ar': '🐪'
        }
        
        # Child-appropriate content filters
        self.inappropriate_words = [
            'violence', 'war', 'death', 'scary', 'fight',
            'hurt', 'sad', 'angry', 'afraid', 'worry'
        ]
        
    def init_cache_db(self):
        """Initialize translation cache database"""
        os.makedirs(os.path.dirname(self.cache_db), exist_ok=True)
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS translation_cache (
                source_text TEXT,
                source_lang TEXT,
                target_lang TEXT,
                translated_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source_text, source_lang, target_lang)
            )
        ''')
        conn.commit()
        conn.close()
    
    def get_cached_translation(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Get translation from cache"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT translated_text FROM translation_cache WHERE source_text=? AND source_lang=? AND target_lang=?',
            (text, source_lang, target_lang)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def cache_translation(self, text: str, source_lang: str, target_lang: str, translation: str):
        """Cache translation result"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO translation_cache (source_text, source_lang, target_lang, translated_text) VALUES (?, ?, ?, ?)',
            (text, source_lang, target_lang, translation)
        )
        conn.commit()
        conn.close()
    
    def make_child_friendly(self, text: str) -> str:
        """Replace inappropriate words with child-friendly alternatives"""
        replacements = {
            'violence': 'disagreement', 'war': 'adventure', 'death': 'sleeping',
            'scary': 'exciting', 'fight': 'competition', 'hurt': 'ouch',
            'sad': 'thoughtful', 'angry': 'frustrated', 'afraid': 'curious',
            'worry': 'wonder'
        }
        
        for word, replacement in replacements.items():
            text = text.replace(word.lower(), replacement)
            text = text.replace(word.capitalize(), replacement.capitalize())
        
        return text
    
    @lru_cache(maxsize=1000)
    def translate_text(self, text: str, target_lang: str, source_lang: str = 'auto') -> Dict:
        """Translate text with caching and child-friendly filtering"""
        try:
            # Check cache first
            cached = self.get_cached_translation(text, source_lang, target_lang)
            if cached:
                return {
                    'success': True,
                    'translated_text': cached,
                    'source_language': source_lang,
                    'target_language': target_lang,
                    'cached': True
                }
            
            # Make request to LibreTranslate
            response = requests.post(
                f"{self.base_url}/translate",
                json={
                    'q': text,
                    'source': source_lang,
                    'target': target_lang,
                    'format': 'text'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result.get('translatedText', text)
                
                # Apply child-friendly filtering
                translated_text = self.make_child_friendly(translated_text)
                
                # Cache the result
                self.cache_translation(text, source_lang, target_lang, translated_text)
                
                return {
                    'success': True,
                    'translated_text': translated_text,
                    'source_language': result.get('detectedLanguage', {}).get('language', source_lang),
                    'target_language': target_lang,
                    'cached': False
                }
            else:
                logger.error(f"Translation API error: {response.status_code}")
                return {
                    'success': False,
                    'error': 'Translation service unavailable',
                    'original_text': text
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Translation request failed: {e}")
            return {
                'success': False,
                'error': 'Network error',
                'original_text': text
            }
        except Exception as e:
            logger.error(f"Unexpected translation error: {e}")
            return {
                'success': False,
                'error': 'Translation failed',
                'original_text': text
            }
    
    def get_supported_languages(self) -> List[Dict]:
        """Get list of supported languages with kid-friendly names"""
        try:
            response = requests.get(f"{self.base_url}/languages", timeout=5)
            if response.status_code == 200:
                languages = response.json()
                # Add kid-friendly elements
                for lang in languages:
                    code = lang.get('code', '')
                    lang['pet_emoji'] = self.language_pets.get(code, '🌍')
                    lang['kid_friendly_name'] = self.get_kid_friendly_language_name(lang.get('name', ''))
                return languages
            else:
                return self.get_default_languages()
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return self.get_default_languages()
    
    def get_default_languages(self) -> List[Dict]:
        """Fallback list of common languages"""
        return [
            {'code': 'en', 'name': 'English', 'pet_emoji': '🐰', 'kid_friendly_name': 'Bunny English'},
            {'code': 'es', 'name': 'Spanish', 'pet_emoji': '🦜', 'kid_friendly_name': 'Parrot Spanish'},
            {'code': 'fr', 'name': 'French', 'pet_emoji': '🐸', 'kid_friendly_name': 'Frog French'},
            {'code': 'de', 'name': 'German', 'pet_emoji': '🐻', 'kid_friendly_name': 'Bear German'},
            {'code': 'it', 'name': 'Italian', 'pet_emoji': '🦊', 'kid_friendly_name': 'Fox Italian'},
            {'code': 'pt', 'name': 'Portuguese', 'pet_emoji': '🐨', 'kid_friendly_name': 'Koala Portuguese'},
            {'code': 'zh', 'name': 'Chinese', 'pet_emoji': '🐼', 'kid_friendly_name': 'Panda Chinese'},
            {'code': 'ja', 'name': 'Japanese', 'pet_emoji': '🐱', 'kid_friendly_name': 'Cat Japanese'},
            {'code': 'hi', 'name': 'Hindi', 'pet_emoji': '🐘', 'kid_friendly_name': 'Elephant Hindi'},
            {'code': 'ar', 'name': 'Arabic', 'pet_emoji': '🐪', 'kid_friendly_name': 'Camel Arabic'}
        ]
    
    def get_kid_friendly_language_name(self, language_name: str) -> str:
        """Convert language names to kid-friendly versions"""
        mapping = {
            'English': 'Bunny English', 'Spanish': 'Parrot Spanish',
            'French': 'Frog French', 'German': 'Bear German',
            'Italian': 'Fox Italian', 'Portuguese': 'Koala Portuguese',
            'Chinese': 'Panda Chinese', 'Japanese': 'Cat Japanese',
            'Hindi': 'Elephant Hindi', 'Arabic': 'Camel Arabic',
            'Russian': 'Wolf Russian', 'Korean': 'Dog Korean'
        }
        return mapping.get(language_name, f"Magic {language_name}")
    
    def translate_lesson_content(self, lesson_data: Dict, target_lang: str) -> Dict:
        """Translate entire lesson content"""
        translated_lesson = lesson_data.copy()
        
        # Translate main content fields
        if 'title' in lesson_data:
            result = self.translate_text(lesson_data['title'], target_lang)
            if result['success']:
                translated_lesson['title'] = result['translated_text']
        
        if 'content' in lesson_data:
            result = self.translate_text(lesson_data['content'], target_lang)
            if result['success']:
                translated_lesson['content'] = result['translated_text']
        
        if 'description' in lesson_data:
            result = self.translate_text(lesson_data['description'], target_lang)
            if result['success']:
                translated_lesson['description'] = result['translated_text']
        
        # Translate questions and answers
        if 'questions' in lesson_data:
            translated_questions = []
            for question in lesson_data['questions']:
                translated_q = question.copy()
                
                if 'question' in question:
                    result = self.translate_text(question['question'], target_lang)
                    if result['success']:
                        translated_q['question'] = result['translated_text']
                
                if 'options' in question:
                    translated_options = []
                    for option in question['options']:
                        result = self.translate_text(option, target_lang)
                        if result['success']:
                            translated_options.append(result['translated_text'])
                        else:
                            translated_options.append(option)
                    translated_q['options'] = translated_options
                
                translated_questions.append(translated_q)
            translated_lesson['questions'] = translated_questions
        
        translated_lesson['translated_to'] = target_lang
        return translated_lesson
    
    def get_language_learning_phrases(self, language_code: str) -> List[Dict]:
        """Get common phrases for language learning"""
        phrases = {
            'en': [
                {'phrase': 'Hello', 'meaning': 'Greeting', 'phonetic': 'heh-LOH'},
                {'phrase': 'Thank you', 'meaning': 'Gratitude', 'phonetic': 'THANK-yoo'},
                {'phrase': 'Please', 'meaning': 'Polite request', 'phonetic': 'PLEEZ'},
                {'phrase': 'I love you', 'meaning': 'Affection', 'phonetic': 'I LUV yoo'},
                {'phrase': 'Good morning', 'meaning': 'Morning greeting', 'phonetic': 'GOOD MOR-ning'}
            ],
            'es': [
                {'phrase': 'Hola', 'meaning': 'Hello', 'phonetic': 'OH-lah'},
                {'phrase': 'Gracias', 'meaning': 'Thank you', 'phonetic': 'GRAH-see-ahs'},
                {'phrase': 'Por favor', 'meaning': 'Please', 'phonetic': 'por fah-VOR'},
                {'phrase': 'Te amo', 'meaning': 'I love you', 'phonetic': 'teh AH-moh'},
                {'phrase': 'Buenos días', 'meaning': 'Good morning', 'phonetic': 'BWAY-nohs DEE-ahs'}
            ],
            'fr': [
                {'phrase': 'Bonjour', 'meaning': 'Hello', 'phonetic': 'bon-ZHOOR'},
                {'phrase': 'Merci', 'meaning': 'Thank you', 'phonetic': 'mer-SEE'},
                {'phrase': 'S\'il vous plaît', 'meaning': 'Please', 'phonetic': 'see voo PLAY'},
                {'phrase': 'Je t\'aime', 'meaning': 'I love you', 'phonetic': 'zhuh TEHM'},
                {'phrase': 'Bonne matinée', 'meaning': 'Good morning', 'phonetic': 'bun ma-tee-NAY'}
            ]
        }
        
        return phrases.get(language_code, phrases['en'])
    
    def detect_language(self, text: str) -> Dict:
        """Detect language of input text"""
        try:
            response = requests.post(
                f"{self.base_url}/detect",
                json={'q': text},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                detected_lang = result[0]['language'] if result else 'en'
                confidence = result[0]['confidence'] if result else 0.5
                
                return {
                    'success': True,
                    'language': detected_lang,
                    'confidence': confidence,
                    'pet_emoji': self.language_pets.get(detected_lang, '🌍'),
                    'kid_friendly_name': self.get_kid_friendly_language_name(detected_lang.title())
                }
            else:
                return {'success': False, 'language': 'en', 'confidence': 0}
                
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {'success': False, 'language': 'en', 'confidence': 0}

# Global translation service instance
translation_service = TranslationService()