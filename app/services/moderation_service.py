import re
import logging
from typing import Dict, List, Optional, Set
from better_profanity import profanity
import sqlite3
import json
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ModerationService:
    def __init__(self):
        self.db_path = "app/data/moderation.db"
        self.init_database()
        
        # Initialize profanity filter with custom words
        profanity.load_censor_words()
        
        # Child-specific inappropriate content patterns
        self.inappropriate_patterns = {
            'personal_info': [
                r'\b\d{3}-\d{3}-\d{4}\b',  # Phone numbers
                r'\b\d{3}\.\d{3}\.\d{4}\b',
                r'\b\d{3} \d{3} \d{4}\b',
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'\b\d{3,5}\s+[A-Za-z\s]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|court|ct|place|pl)\b',  # Addresses
                r'\b\d{5}(?:-\d{4})?\b'  # ZIP codes
            ],
            'cyberbullying': [
                r'\b(?:you\s+are|you\'re|ur)\s+(?:stupid|dumb|ugly|fat|weird|loser|freak)\b',
                r'\b(?:hate|kill|die|stupid|dumb|ugly|fat|worthless|useless)\b',
                r'\b(?:nobody\s+likes|everyone\s+hates)\s+you\b',
                r'\b(?:go\s+away|leave\s+me\s+alone|shut\s+up)\b'
            ],
            'inappropriate_content': [
                r'\b(?:sex|sexy|naked|nude|porn|xxx)\b',
                r'\b(?:drugs|alcohol|beer|wine|marijuana|weed)\b',
                r'\b(?:violence|fight|hit|punch|kick|hurt)\b'
            ],
            'stranger_danger': [
                r'\b(?:meet\s+me|come\s+to|my\s+address|where\s+do\s+you\s+live)\b',
                r'\b(?:secret|don\'t\s+tell|between\s+us|our\s+secret)\b',
                r'\b(?:send\s+me|show\s+me|picture|photo|pic)\b'
            ]
        }
        
        # Positive replacement suggestions
        self.positive_replacements = {
            'stupid': 'silly', 'dumb': 'confused', 'hate': 'dislike',
            'ugly': 'different', 'fat': 'big', 'weird': 'unique',
            'loser': 'learner', 'freak': 'special', 'shut up': 'please be quiet',
            'go away': 'I need space', 'die': 'go to sleep', 'kill': 'stop'
        }
        
        # Wholesome content suggestions
        self.wholesome_suggestions = [
            "How about we talk about your favorite animals? 🐾",
            "Tell me about something fun you did today! 🌟",
            "What's your favorite color and why? 🌈",
            "Let's create a happy story together! 📚",
            "What makes you feel proud of yourself? 🏆",
            "Tell me about your pet friend! What do they like to do? 🐕"
        ]
        
        # Educational content flags
        self.educational_flags = {
            'learning_opportunity': [
                'kindness', 'sharing', 'helping', 'friendship', 'respect',
                'empathy', 'compassion', 'understanding', 'patience', 'cooperation'
            ],
            'emotional_learning': [
                'feelings', 'emotions', 'happy', 'sad', 'angry', 'scared',
                'proud', 'excited', 'worried', 'confused', 'calm'
            ]
        }
    
    def init_database(self):
        """Initialize moderation database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Moderation logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS moderation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                original_text TEXT,
                filtered_text TEXT,
                flags TEXT,
                severity_level INTEGER,
                action_taken TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Positive interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positive_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                interaction_text TEXT,
                positive_score REAL,
                educational_value TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Safety alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS safety_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                alert_type TEXT,
                content TEXT,
                severity INTEGER,
                handled BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def moderate_content(self, text: str, user_id: int, context: str = 'chat') -> Dict:
        """Comprehensive content moderation for children"""
        try:
            original_text = text
            flags = []
            severity = 0
            filtered_text = text
            
            # Check for profanity
            if profanity.contains_profanity(text):
                flags.append('profanity')
                severity = max(severity, 2)
                filtered_text = profanity.censor(filtered_text)
            
            # Check for inappropriate patterns
            for category, patterns in self.inappropriate_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text.lower()):
                        flags.append(category)
                        severity = max(severity, 3 if category == 'stranger_danger' else 2)
                        filtered_text = re.sub(pattern, '[FILTERED]', filtered_text, flags=re.IGNORECASE)
            
            # Apply positive replacements
            filtered_text = self.apply_positive_replacements(filtered_text)
            
            # Check for educational opportunities
            educational_value = self.identify_educational_opportunities(text)
            
            # Generate appropriate response
            response = self.generate_moderation_response(flags, severity, educational_value)
            
            # Log the moderation action
            self.log_moderation_action(user_id, original_text, filtered_text, flags, severity, context)
            
            # Handle high-severity content
            if severity >= 3:
                self.create_safety_alert(user_id, original_text, flags, severity)
            
            # Track positive interactions
            if not flags and educational_value:
                self.log_positive_interaction(user_id, text, educational_value)
            
            return {
                'success': True,
                'filtered_text': filtered_text,
                'flags': flags,
                'severity': severity,
                'safe_for_children': severity < 3,
                'response': response,
                'educational_opportunity': educational_value,
                'suggested_topic': self.suggest_alternative_topic(flags) if flags else None
            }
            
        except Exception as e:
            logger.error(f"Content moderation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'filtered_text': text,
                'safe_for_children': False
            }
    
    def apply_positive_replacements(self, text: str) -> str:
        """Replace negative words with positive alternatives"""
        words = text.split()
        replaced_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in self.positive_replacements:
                # Preserve original capitalization
                replacement = self.positive_replacements[clean_word]
                if word[0].isupper():
                    replacement = replacement.capitalize()
                replaced_words.append(replacement)
            else:
                replaced_words.append(word)
        
        return ' '.join(replaced_words)
    
    def identify_educational_opportunities(self, text: str) -> Optional[str]:
        """Identify opportunities for educational content"""
        text_lower = text.lower()
        
        for category, keywords in self.educational_flags.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        
        return None
    
    def generate_moderation_response(self, flags: List[str], severity: int, educational_value: Optional[str]) -> str:
        """Generate appropriate response based on moderation results"""
        if severity >= 3:
            return ("I want to keep our conversation safe and fun! 🛡️ "
                   "Let's talk about something positive instead! "
                   f"{self.get_random_wholesome_suggestion()}")
        
        elif severity >= 2:
            return ("Let's use kind words that make everyone feel good! 😊 "
                   "How about we talk about something that makes you happy?")
        
        elif 'profanity' in flags:
            return ("Oops! Let's use our best words! ✨ "
                   "What's something awesome you'd like to share?")
        
        elif educational_value:
            if educational_value == 'learning_opportunity':
                return ("I love hearing about kindness and friendship! 💝 "
                       "Tell me more about that!")
            elif educational_value == 'emotional_learning':
                return ("Feelings are so important to talk about! 💙 "
                       "Your pet friend wants to understand how you feel!")
        
        return ""  # No response needed for clean content
    
    def suggest_alternative_topic(self, flags: List[str]) -> str:
        """Suggest alternative topics based on flags"""
        suggestions = {
            'personal_info': "Instead of sharing personal details, tell me about your hobbies! 🎨",
            'cyberbullying': "Let's focus on being kind to each other! What makes you feel happy? 😊",
            'inappropriate_content': "How about we talk about your favorite books or games? 📚🎮",
            'stranger_danger': "Let's keep our conversations safe! What's your favorite animal? 🐾"
        }
        
        for flag in flags:
            if flag in suggestions:
                return suggestions[flag]
        
        return self.get_random_wholesome_suggestion()
    
    def get_random_wholesome_suggestion(self) -> str:
        """Get a random wholesome conversation suggestion"""
        import random
        return random.choice(self.wholesome_suggestions)
    
    def log_moderation_action(self, user_id: int, original_text: str, filtered_text: str, 
                            flags: List[str], severity: int, context: str):
        """Log moderation action to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO moderation_logs 
            (user_id, original_text, filtered_text, flags, severity_level, action_taken)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, original_text, filtered_text, json.dumps(flags), severity, context))
        
        conn.commit()
        conn.close()
    
    def log_positive_interaction(self, user_id: int, text: str, educational_value: str):
        """Log positive interactions for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate positive score based on educational keywords
        positive_score = self.calculate_positive_score(text)
        
        cursor.execute('''
            INSERT INTO positive_interactions 
            (user_id, interaction_text, positive_score, educational_value)
            VALUES (?, ?, ?, ?)
        ''', (user_id, text, positive_score, educational_value))
        
        conn.commit()
        conn.close()
    
    def calculate_positive_score(self, text: str) -> float:
        """Calculate positivity score of text"""
        positive_words = [
            'happy', 'joy', 'love', 'kind', 'nice', 'good', 'great', 'awesome',
            'wonderful', 'amazing', 'fantastic', 'brilliant', 'excellent', 'perfect',
            'friend', 'help', 'share', 'care', 'thank', 'please', 'sorry',
            'learn', 'discover', 'explore', 'create', 'imagine', 'dream'
        ]
        
        text_lower = text.lower()
        score = 0
        
        for word in positive_words:
            if word in text_lower:
                score += 1
        
        # Normalize by text length
        words_count = len(text.split())
        return min(score / max(words_count, 1), 1.0)
    
    def create_safety_alert(self, user_id: int, content: str, flags: List[str], severity: int):
        """Create safety alert for high-severity content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        alert_type = 'high_severity' if severity >= 4 else 'moderate_concern'
        
        cursor.execute('''
            INSERT INTO safety_alerts (user_id, alert_type, content, severity)
            VALUES (?, ?, ?, ?)
        ''', (user_id, alert_type, content, severity))
        
        conn.commit()
        conn.close()
        
        # Log for immediate attention
        logger.warning(f"Safety alert created for user {user_id}: {flags}")
    
    def get_user_safety_report(self, user_id: int, days: int = 7) -> Dict:
        """Generate safety report for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get moderation history
        cursor.execute('''
            SELECT flags, severity_level, timestamp
            FROM moderation_logs 
            WHERE user_id=? AND timestamp > datetime('now', '-{} days')
            ORDER BY timestamp DESC
        '''.format(days), (user_id,))
        
        moderation_history = cursor.fetchall()
        
        # Get positive interactions
        cursor.execute('''
            SELECT positive_score, educational_value, timestamp
            FROM positive_interactions
            WHERE user_id=? AND timestamp > datetime('now', '-{} days')
            ORDER BY timestamp DESC
        '''.format(days), (user_id,))
        
        positive_interactions = cursor.fetchall()
        
        conn.close()
        
        # Analyze data
        total_interactions = len(moderation_history) + len(positive_interactions)
        flagged_interactions = len([m for m in moderation_history if json.loads(m[0])])
        positive_ratio = len(positive_interactions) / max(total_interactions, 1)
        
        safety_score = max(0, min(100, (positive_ratio * 100) - (flagged_interactions * 10)))
        
        return {
            'user_id': user_id,
            'period_days': days,
            'total_interactions': total_interactions,
            'positive_interactions': len(positive_interactions),
            'flagged_interactions': flagged_interactions,
            'safety_score': round(safety_score, 1),
            'status': 'excellent' if safety_score >= 90 else 'good' if safety_score >= 70 else 'needs_attention',
            'recommendations': self.get_safety_recommendations(safety_score, flagged_interactions)
        }
    
    def get_safety_recommendations(self, safety_score: float, flagged_count: int) -> List[str]:
        """Get safety recommendations based on user behavior"""
        recommendations = []
        
        if safety_score >= 90:
            recommendations.append("🌟 Excellent online behavior! Keep being kind and positive!")
            recommendations.append("🏆 You're a great example of how to communicate safely online!")
        elif safety_score >= 70:
            recommendations.append("😊 Good job staying safe online! Keep up the positive interactions!")
            recommendations.append("💡 Remember to always use kind words in your conversations!")
        else:
            recommendations.append("💙 Let's focus on using kind, positive language!")
            recommendations.append("🛡️ Remember our safety rules: be kind, be respectful, be safe!")
            recommendations.append("🌈 Try talking about things that make you happy!")
        
        if flagged_count > 0:
            recommendations.append("📚 Review our community guidelines with a trusted adult!")
            recommendations.append("🤝 Ask a grown-up for help if you're unsure about something!")
        
        return recommendations
    
    def validate_story_content(self, story_text: str, user_id: int) -> Dict:
        """Special validation for collaborative storytelling"""
        # Standard moderation
        moderation_result = self.moderate_content(story_text, user_id, 'story')
        
        # Additional story-specific checks
        story_appropriate = self.check_story_appropriateness(story_text)
        creative_value = self.assess_creative_value(story_text)
        
        return {
            **moderation_result,
            'story_appropriate': story_appropriate,
            'creative_value': creative_value,
            'story_suggestions': self.get_story_improvement_suggestions(story_text)
        }
    
    def check_story_appropriateness(self, text: str) -> bool:
        """Check if story content is appropriate for children"""
        inappropriate_themes = [
            'violence', 'death', 'scary', 'nightmare', 'monster', 'ghost',
            'war', 'fight', 'blood', 'hurt', 'pain', 'sad ending'
        ]
        
        text_lower = text.lower()
        for theme in inappropriate_themes:
            if theme in text_lower:
                return False
        
        return True
    
    def assess_creative_value(self, text: str) -> float:
        """Assess the creative value of story content"""
        creative_elements = [
            'magic', 'adventure', 'friendship', 'hero', 'quest', 'journey',
            'discover', 'treasure', 'rainbow', 'castle', 'forest', 'ocean',
            'flying', 'dragon', 'unicorn', 'fairy', 'princess', 'prince'
        ]
        
        text_lower = text.lower()
        score = 0
        
        for element in creative_elements:
            if element in text_lower:
                score += 1
        
        return min(score / 5.0, 1.0)  # Normalize to 0-1 scale
    
    def get_story_improvement_suggestions(self, text: str) -> List[str]:
        """Get suggestions to improve story content"""
        suggestions = []
        
        if len(text.split()) < 10:
            suggestions.append("Try adding more details to make your story more exciting! 📝")
        
        if not any(word in text.lower() for word in ['happy', 'joy', 'fun', 'smile', 'laugh']):
            suggestions.append("How about adding something that makes the characters happy? 😊")
        
        if not any(word in text.lower() for word in ['friend', 'help', 'kind', 'care', 'share']):
            suggestions.append("Maybe include friendship or helping others in your story! 🤝")
        
        if not suggestions:
            suggestions.append("Your story is great! Keep being creative! ✨")
        
        return suggestions

# Global moderation service instance
moderation_service = ModerationService()