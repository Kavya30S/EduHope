import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from textblob import TextBlob
import re
import os
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)

class SentimentService:
    def __init__(self):
        self.db_path = "app/data/sentiment_analysis.db"
        self.init_database()
        
        # Child-specific emotion keywords
        self.emotion_keywords = {
            'happy': ['happy', 'joy', 'excited', 'fun', 'great', 'awesome', 'love', 'smile', 'laugh'],
            'sad': ['sad', 'upset', 'cry', 'lonely', 'miss', 'hurt', 'disappointed'],
            'angry': ['angry', 'mad', 'frustrated', 'annoyed', 'hate', 'grr'],
            'scared': ['scared', 'afraid', 'worry', 'nervous', 'frightened', 'anxious'],
            'confused': ['confused', 'don\'t understand', 'help', 'stuck', 'difficult'],
            'proud': ['proud', 'achievement', 'accomplished', 'success', 'win', 'good job'],
            'curious': ['curious', 'wonder', 'question', 'learn', 'explore', 'discover'],
            'calm': ['calm', 'peaceful', 'relaxed', 'content', 'quiet', 'okay']
        }
        
        # Emotion response templates for children
        self.emotion_responses = {
            'happy': [
                "I'm so glad you're feeling happy! 🌟 Your joy makes your pet friend happy too!",
                "Yay! Happiness is contagious! ✨ Keep spreading those good vibes!",
                "Your happiness lights up the whole world! 🌈 What made you feel so great?"
            ],
            'sad': [
                "I notice you might be feeling a bit down. 💙 That's okay, everyone feels sad sometimes.",
                "Sending you a virtual hug! 🤗 Would you like to play with your pet to feel better?",
                "It's brave to share when you're feeling sad. 💕 Let's find something fun to do together!"
            ],
            'angry': [
                "I can tell you might be feeling frustrated. 😤 Take a deep breath with me - in... and out...",
                "Angry feelings are normal! 🌊 Let's turn that energy into something positive!",
                "When we feel mad, it helps to talk about it. 💪 You're doing great by expressing yourself!"
            ],
            'scared': [
                "Feeling scared is completely normal! 🦸 You're braver than you think!",
                "Your pet friend is here to keep you company! 🐾 You're not alone!",
                "Take a deep breath. 🌸 You're safe here, and we're here to help you feel better!"
            ],
            'confused': [
                "Questions are awesome! 🤔 They help us learn and grow!",
                "It's totally okay to feel confused sometimes! 🧩 Let's figure this out together!",
                "Asking for help shows how smart you are! 🌟 What would you like to understand better?"
            ],
            'proud': [
                "Wow! You should feel proud! 🏆 Your achievements are amazing!",
                "Look at you go! 🎉 Your hard work is really paying off!",
                "You're doing such a great job! ⭐ Your pet is so proud of you too!"
            ],
            'curious': [
                "I love your curiosity! 🔍 Curious minds discover the most amazing things!",
                "Questions are the key to learning! 🗝️ What adventure shall we explore today?",
                "Your curiosity is a superpower! 🦸‍♀️ Let's discover something new together!"
            ],
            'calm': [
                "You seem peaceful and content! 🕊️ That's a wonderful feeling!",
                "Your calm energy is so nice! 🌺 It helps create a happy space for everyone!",
                "Feeling balanced and okay is beautiful! 🌿 You're doing great!"
            ]
        }
        
        # Crisis intervention keywords
        self.crisis_keywords = [
            'want to die', 'kill myself', 'end it all', 'can\'t go on',
            'nobody loves me', 'everyone hates me', 'worthless', 'useless'
        ]
        
        # Positive reinforcement triggers
        self.achievement_keywords = [
            'finished', 'completed', 'learned', 'understood', 'figured out',
            'solved', 'got it right', 'passed', 'succeeded'
        ]
    
    def init_database(self):
        """Initialize sentiment analysis database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Emotion tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emotion_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text_input TEXT,
                detected_emotion TEXT,
                sentiment_score REAL,
                confidence REAL,
                context TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                intervention_triggered BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Mood patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mood_patterns (
                user_id INTEGER,
                date DATE,
                dominant_emotion TEXT,
                average_sentiment REAL,
                emotion_counts TEXT,
                activities_completed INTEGER,
                PRIMARY KEY (user_id, date)
            )
        ''')
        
        # Crisis alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crisis_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                alert_text TEXT,
                severity_level INTEGER,
                handled BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def analyze_text_sentiment(self, text: str, user_id: int, context: str = 'general') -> Dict:
        """Analyze sentiment of user text input"""
        try:
            # Clean and preprocess text
            cleaned_text = self.preprocess_text(text)
            
            # Use TextBlob for basic sentiment analysis
            blob = TextBlob(cleaned_text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Detect specific emotions
            detected_emotions = self.detect_emotions(cleaned_text)
            primary_emotion = max(detected_emotions.items(), key=lambda x: x[1])[0] if detected_emotions else 'neutral'
            
            # Check for crisis indicators
            crisis_detected = self.check_crisis_indicators(cleaned_text)
            
            # Generate appropriate response
            response = self.generate_emotional_response(primary_emotion, polarity, crisis_detected)
            
            # Log the analysis
            self.log_emotion_analysis(user_id, text, primary_emotion, polarity, subjectivity, context, crisis_detected)
            
            # Update mood patterns
            self.update_mood_patterns(user_id, primary_emotion, polarity)
            
            return {
                'success': True,
                'sentiment_score': polarity,
                'confidence': subjectivity,
                'primary_emotion': primary_emotion,
                'all_emotions': detected_emotions,
                'response': response,
                'crisis_detected': crisis_detected,
                'recommendations': self.get_activity_recommendations(primary_emotion, polarity)
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "I'm here to listen! 💙 Tell me more about how you're feeling!"
            }
    
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Handle common misspellings and kid language
        replacements = {
            'gud': 'good', 'grate': 'great', 'luv': 'love',
            'ur': 'your', 'u': 'you', 'r': 'are',
            'bc': 'because', 'wanna': 'want to', 'gonna': 'going to'
        }
        
        for old, new in replacements.items():
            text = re.sub(r'\b' + old + r'\b', new, text)
        
        return text
    
    def detect_emotions(self, text: str) -> Dict[str, float]:
        """Detect specific emotions in text"""
        emotion_scores = defaultdict(float)
        words = text.split()
        
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    # Give higher weight to exact matches
                    if keyword in words:
                        emotion_scores[emotion] += 1.0
                    else:
                        emotion_scores[emotion] += 0.5
        
        # Normalize scores
        if emotion_scores:
            max_score = max(emotion_scores.values())
            for emotion in emotion_scores:
                emotion_scores[emotion] /= max_score
        
        return dict(emotion_scores)
    
    def check_crisis_indicators(self, text: str) -> bool:
        """Check for crisis intervention indicators"""
        for keyword in self.crisis_keywords:
            if keyword in text.lower():
                return True
        return False
    
    def generate_emotional_response(self, emotion: str, sentiment_score: float, crisis_detected: bool) -> str:
        """Generate appropriate emotional response"""
        if crisis_detected:
            return ("I'm really glad you shared that with me. 💙 You're so important and valued! "
                   "Let's talk to a grown-up who can help, okay? You're not alone! 🤗")
        
        responses = self.emotion_responses.get(emotion, self.emotion_responses['calm'])
        
        # Choose response based on sentiment intensity
        if sentiment_score > 0.5:
            return responses[0]  # Most positive response
        elif sentiment_score < -0.5:
            return responses[-1] if len(responses) > 1 else responses[0]  # Most supportive response
        else:
            return responses[len(responses)//2] if len(responses) > 2 else responses[0]  # Balanced response
    
    def get_activity_recommendations(self, emotion: str, sentiment_score: float) -> List[Dict]:
        """Get activity recommendations based on emotional state"""
        activities = {
            'happy': [
                {'activity': 'Share your joy with your pet!', 'icon': '🐾', 'points': 10},
                {'activity': 'Create a happy story!', 'icon': '📚', 'points': 15},
                {'activity': 'Teach your pet a new dance!', 'icon': '💃', 'points': 12}
            ],
            'sad': [
                {'activity': 'Hug your virtual pet!', 'icon': '🤗', 'points': 8},
                {'activity': 'Listen to calming music together!', 'icon': '🎵', 'points': 10},
                {'activity': 'Draw your feelings!', 'icon': '🎨', 'points': 12}
            ],
            'angry': [
                {'activity': 'Take deep breaths with your pet!', 'icon': '🌬️', 'points': 15},
                {'activity': 'Play a calming puzzle game!', 'icon': '🧩', 'points': 10},
                {'activity': 'Write in your journal!', 'icon': '📝', 'points': 12}
            ],
            'scared': [
                {'activity': 'Your pet will protect you!', 'icon': '🛡️', 'points': 10},
                {'activity': 'Practice brave affirmations!', 'icon': '💪', 'points': 15},
                {'activity': 'Create a safe space story!', 'icon': '🏰', 'points': 12}
            ],
            'confused': [
                {'activity': 'Ask your pet for help!', 'icon': '❓', 'points': 8},
                {'activity': 'Break it down into smaller steps!', 'icon': '👣', 'points': 12},
                {'activity': 'Try a learning game!', 'icon': '🎮', 'points': 15}
            ],
            'proud': [
                {'activity': 'Celebrate with your pet!', 'icon': '🎉', 'points': 15},
                {'activity': 'Share your achievement!', 'icon': '🏆', 'points': 12},
                {'activity': 'Unlock new pet accessories!', 'icon': '✨', 'points': 20}
            ]
        }
        
        return activities.get(emotion, activities['happy'])
    
    def log_emotion_analysis(self, user_id: int, text: str, emotion: str, 
                           sentiment_score: float, confidence: float, 
                           context: str, crisis_detected: bool):
        """Log emotion analysis to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO emotion_logs 
            (user_id, text_input, detected_emotion, sentiment_score, confidence, context, intervention_triggered)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, text, emotion, sentiment_score, confidence, context, crisis_detected))
        
        if crisis_detected:
            cursor.execute('''
                INSERT INTO crisis_alerts (user_id, alert_text, severity_level)
                VALUES (?, ?, ?)
            ''', (user_id, text, 3))  # High severity
        
        conn.commit()
        conn.close()
    
    def update_mood_patterns(self, user_id: int, emotion: str, sentiment_score: float):
        """Update daily mood patterns"""
        today = datetime.now().date()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get existing pattern for today
        cursor.execute('''
            SELECT emotion_counts, average_sentiment, activities_completed
            FROM mood_patterns WHERE user_id=? AND date=?
        ''', (user_id, today))
        
        result = cursor.fetchone()
        
        if result:
            # Update existing pattern
            emotion_counts = json.loads(result[0]) if result[0] else {}
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            # Update average sentiment
            new_avg = (result[1] + sentiment_score) / 2
            
            cursor.execute('''
                UPDATE mood_patterns 
                SET emotion_counts=?, average_sentiment=?, dominant_emotion=?
                WHERE user_id=? AND date=?
            ''', (json.dumps(emotion_counts), new_avg, 
                  max(emotion_counts.items(), key=lambda x: x[1])[0], user_id, today))
        else:
            # Create new pattern
            emotion_counts = {emotion: 1}
            cursor.execute('''
                INSERT INTO mood_patterns 
                (user_id, date, dominant_emotion, average_sentiment, emotion_counts, activities_completed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, today, emotion, sentiment_score, json.dumps(emotion_counts), 0))
        
        conn.commit()
        conn.close()
    
    def get_mood_insights(self, user_id: int, days: int = 7) -> Dict:
        """Get mood insights for the past N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        cursor.execute('''
            SELECT date, dominant_emotion, average_sentiment, emotion_counts
            FROM mood_patterns 
            WHERE user_id=? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        ''', (user_id, start_date, end_date))
        
        patterns = cursor.fetchall()
        
        if not patterns:
            return {
                'success': False,
                'message': "Not enough data yet! Keep chatting with your pet to see your mood patterns! 🌟"
            }
        
        # Analyze patterns
        emotions = [p[1] for p in patterns]
        sentiments = [p[2] for p in patterns]
        
        # Most common emotion
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        most_common_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        
        # Average sentiment
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Trend analysis
        if len(sentiments) >= 3:
            recent_trend = sum(sentiments[-3:]) / 3
            earlier_trend = sum(sentiments[:-3]) / len(sentiments[:-3]) if len(sentiments) > 3 else avg_sentiment
            trend_direction = "improving" if recent_trend > earlier_trend else "stable" if abs(recent_trend - earlier_trend) < 0.1 else "needs attention"
        else:
            trend_direction = "stable"
        
        conn.close()
        
        return {
            'success': True,
            'most_common_emotion': most_common_emotion,
            'average_sentiment': avg_sentiment,
            'trend_direction': trend_direction,
            'days_analyzed': len(patterns),
            'mood_summary': self.generate_mood_summary(most_common_emotion, avg_sentiment, trend_direction),
            'pet_message': self.generate_pet_mood_message(most_common_emotion, trend_direction)
        }
    
    def generate_mood_summary(self, emotion: str, sentiment: float, trend: str) -> str:
        """Generate a child-friendly mood summary"""
        emotion_descriptions = {
            'happy': 'full of sunshine and joy',
            'sad': 'having some cloudy moments',
            'angry': 'feeling fiery and strong',
            'scared': 'feeling cautious and careful',
            'confused': 'curious and wondering',
            'proud': 'confident and accomplished',
            'curious': 'excited to explore and learn',
            'calm': 'peaceful and balanced'
        }
        
        base_description = emotion_descriptions.get(emotion, 'experiencing many different feelings')
        
        if trend == "improving":
            return f"You've been {base_description}, and things are getting brighter! ✨"
        elif trend == "needs attention":
            return f"You've been {base_description}. Your pet thinks you're amazing and wants to help! 💙"
        else:
            return f"You've been {base_description}, staying steady and strong! 🌟"
    
    def generate_pet_mood_message(self, emotion: str, trend: str) -> str:
        """Generate a message from the pet based on mood"""
        messages = {
            'happy': [
                "Your happiness makes me so happy too! Let's play together! 🎾",
                "I love seeing you smile! Want to go on an adventure? 🗺️",
                "Your joy is contagious! I'm wagging my tail with excitement! 🐕"
            ],
            'sad': [
                "I'm here for you always. Want to cuddle? 🤗",
                "Even when you're sad, you're still amazing to me! 💙",
                "Let's find something fun to do together, okay? 🎈"
            ],
            'angry': [
                "I understand you're feeling strong emotions. I'm here! 🦁",
                "Your feelings are valid! Let's channel that energy into play! ⚡",
                "Take deep breaths with me - we're a team! 🌊"
            ],
            'scared': [
                "I'll be your brave companion! We can face anything together! 🛡️",
                "You're braver than you know! I believe in you! 💪",
                "I'm right here beside you. You're never alone! 🌟"
            ]
        }
        
        emotion_messages = messages.get(emotion, messages['happy'])
        
        if trend == "improving":
            return emotion_messages[0] + " You're doing so well! 📈"
        elif trend == "needs attention":
            return emotion_messages[-1] + " Let's work on this together! 🤝"
        else:
            return emotion_messages[len(emotion_messages)//2]
    
    def get_crisis_support_resources(self) -> Dict:
        """Get age-appropriate crisis support resources"""
        return {
            'immediate_help': {
                'message': "If you're feeling really sad or scared, please talk to a trusted grown-up right away! 🤗",
                'actions': [
                    "Find a parent, teacher, or other trusted adult",
                    "Call a helpline with a grown-up's help",
                    "Remember: You are loved and important! 💙"
                ]
            },
            'coping_strategies': [
                {'strategy': 'Deep breathing', 'description': 'Breathe in slowly, hold, breathe out slowly', 'icon': '🌬️'},
                {'strategy': 'Count to 10', 'description': 'Count slowly and focus on the numbers', 'icon': '🔢'},
                {'strategy': 'Hug something soft', 'description': 'Hug a pillow, stuffed animal, or pet', 'icon': '🧸'},
                {'strategy': 'Talk to someone', 'description': 'Share your feelings with someone you trust', 'icon': '💬'},
                {'strategy': 'Write or draw', 'description': 'Express your feelings through art or writing', 'icon': '🎨'}
            ],
            'positive_affirmations': [
                "I am brave and strong! 💪",
                "I am loved and important! 💙",
                "This feeling will pass! 🌈",
                "I can handle difficult things! 🌟",
                "I have people who care about me! 🤗"
            ]
        }
    
    def emotional_check_in(self, user_id: int) -> Dict:
        """Perform a quick emotional check-in"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent emotional data
        cursor.execute('''
            SELECT detected_emotion, sentiment_score, timestamp
            FROM emotion_logs 
            WHERE user_id=? AND timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (user_id,))
        
        recent_emotions = cursor.fetchall()
        conn.close()
        
        if not recent_emotions:
            return {
                'check_in_needed': True,
                'message': "Hi there! 👋 How are you feeling today? Your pet wants to know!",
                'suggested_activities': self.get_activity_recommendations('curious', 0.5)
            }
        
        # Analyze recent emotional state
        recent_sentiment = sum(e[1] for e in recent_emotions) / len(recent_emotions)
        recent_emotion_counts = {}
        for emotion_data in recent_emotions:
            emotion = emotion_data[0]
            recent_emotion_counts[emotion] = recent_emotion_counts.get(emotion, 0) + 1
        
        dominant_recent_emotion = max(recent_emotion_counts.items(), key=lambda x: x[1])[0]
        
        # Determine if check-in is needed
        check_in_needed = (
            recent_sentiment < -0.3 or  # Negative sentiment
            dominant_recent_emotion in ['sad', 'angry', 'scared'] or  # Concerning emotions
            len(recent_emotions) < 3  # Low engagement
        )
        
        if check_in_needed:
            return {
                'check_in_needed': True,
                'message': f"I notice you might be feeling {dominant_recent_emotion}. 💙 Want to talk about it?",
                'suggested_activities': self.get_activity_recommendations(dominant_recent_emotion, recent_sentiment),
                'encouragement': self.generate_encouragement_message(dominant_recent_emotion)
            }
        else:
            return {
                'check_in_needed': False,
                'message': f"You seem to be doing well! 🌟 Keep up the great work!",
                'celebration': f"Your {dominant_recent_emotion} energy is wonderful! ✨",
                'suggested_activities': self.get_activity_recommendations(dominant_recent_emotion, recent_sentiment)
            }
    
    def generate_encouragement_message(self, emotion: str) -> str:
        """Generate encouraging message based on emotion"""
        encouragements = {
            'sad': "Remember, every cloud has a silver lining! 🌤️ You're stronger than you know!",
            'angry': "Your feelings are valid! 💪 Let's turn that energy into something amazing!",
            'scared': "Courage isn't about not being scared - it's about being scared and doing it anyway! 🦸",
            'confused': "Every expert was once a beginner! 🌱 Questions are the first step to learning!",
            'happy': "Your happiness is contagious! ✨ Keep spreading those good vibes!",
            'proud': "You have every reason to be proud! 🏆 Your achievements are inspiring!",
            'curious': "Curiosity is the engine of learning! 🚀 Keep exploring and discovering!",
            'calm': "Your peaceful energy is beautiful! 🕊️ You're creating a happy space for everyone!"
        }
        
        return encouragements.get(emotion, "You're doing amazing! 🌟 Keep being awesome!")

# Global sentiment service instance
sentiment_service = SentimentService()