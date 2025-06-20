import json
import numpy as np
from datetime import datetime, timedelta
from textblob import TextBlob
import cv2
import mediapipe as mp
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from app.models.emotion import EmotionLog
from app.models.user import User
from app import db
import logging

class EmotionAIService:
    def __init__(self):
        """Initialize emotion AI service with real-time learning capabilities"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize emotion detection models
        self.emotion_classifier = pipeline(
            "text-classification", 
            model="j-hartmann/emotion-english-distilroberta-base",
            return_all_scores=True
        )
        
        # Face detection for video emotion analysis
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.5)
        
        # Real-time learning storage
        self.user_emotion_patterns = {}
        self.learning_buffer = {}
        
        # Child-friendly emotion categories
        self.child_emotions = {
            'happy': {'emoji': '😊', 'color': '#FFD700', 'level': 'amazing'},
            'excited': {'emoji': '🤩', 'color': '#FF6B6B', 'level': 'super'},
            'calm': {'emoji': '😌', 'color': '#87CEEB', 'level': 'peaceful'},
            'curious': {'emoji': '🤔', 'color': '#98FB98', 'level': 'wondering'},
            'sad': {'emoji': '😢', 'color': '#B0C4DE', 'level': 'blue'},
            'worried': {'emoji': '😰', 'color': '#DDA0DD', 'level': 'troubled'},
            'frustrated': {'emoji': '😤', 'color': '#FFA07A', 'level': 'stuck'},
            'proud': {'emoji': '😊', 'color': '#FFB6C1', 'level': 'accomplished'}
        }
        
    def analyze_text_emotion(self, text, user_id):
        """Analyze emotion from text with personalized learning"""
        try:
            # Get base emotion analysis
            emotions = self.emotion_classifier(text)
            
            # Apply personalized learning if user data exists
            if user_id in self.user_emotion_patterns:
                emotions = self._apply_personalized_weights(emotions, user_id)
            
            # Convert to child-friendly format
            child_emotion = self._convert_to_child_emotion(emotions)
            
            # Store for learning
            self._store_emotion_data(user_id, text, child_emotion, 'text')
            
            return child_emotion
            
        except Exception as e:
            self.logger.error(f"Text emotion analysis error: {e}")
            return self._get_default_emotion()
    
    def analyze_voice_emotion(self, audio_features, user_id):
        """Analyze emotion from voice patterns"""
        try:
            # Extract features from audio
            pitch_variance = np.var(audio_features.get('pitch', []))
            energy_level = np.mean(audio_features.get('energy', []))
            speaking_rate = audio_features.get('rate', 1.0)
            
            # Determine emotion based on audio features
            emotion_score = self._calculate_voice_emotion_score(
                pitch_variance, energy_level, speaking_rate
            )
            
            child_emotion = self._voice_score_to_emotion(emotion_score)
            
            # Store for learning
            self._store_emotion_data(user_id, audio_features, child_emotion, 'voice')
            
            return child_emotion
            
        except Exception as e:
            self.logger.error(f"Voice emotion analysis error: {e}")
            return self._get_default_emotion()
    
    def analyze_facial_emotion(self, image_data, user_id):
        """Analyze emotion from facial expressions"""
        try:
            # Convert image data to OpenCV format
            image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            results = self.face_detection.process(rgb_image)
            
            if results.detections:
                # Extract facial features and analyze emotion
                emotion_data = self._extract_facial_features(results.detections[0], rgb_image)
                child_emotion = self._facial_features_to_emotion(emotion_data)
                
                # Store for learning
                self._store_emotion_data(user_id, emotion_data, child_emotion, 'facial')
                
                return child_emotion
            else:
                return self._get_default_emotion()
                
        except Exception as e:
            self.logger.error(f"Facial emotion analysis error: {e}")
            return self._get_default_emotion()
    
    def get_emotional_support_response(self, emotion, user_id, context="general"):
        """Generate personalized emotional support response"""
        try:
            user = User.query.get(user_id)
            if not user:
                return self._get_generic_support_response(emotion)
            
            # Get user's emotion history for personalization
            recent_emotions = self._get_recent_emotions(user_id)
            
            # Generate personalized response based on patterns
            support_response = self._generate_support_response(
                emotion, user.age, recent_emotions, context
            )
            
            # Include pet companion support if user has one
            if user.pet:
                support_response['pet_message'] = self._get_pet_support_message(
                    emotion, user.pet.pet_type
                )
            
            return support_response
            
        except Exception as e:
            self.logger.error(f"Support response error: {e}")
            return self._get_generic_support_response(emotion)
    
    def update_learning_model(self, user_id, feedback_data):
        """Update personalized emotion model based on user feedback"""
        try:
            if user_id not in self.user_emotion_patterns:
                self.user_emotion_patterns[user_id] = {
                    'weights': {},
                    'patterns': {},
                    'accuracy': 0.0,
                    'last_updated': datetime.now()
                }
            
            # Process feedback and update weights
            self._process_feedback(user_id, feedback_data)
            
            # Retrain if enough data collected
            if self._should_retrain(user_id):
                self._retrain_user_model(user_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Learning update error: {e}")
            return False
    
    def get_emotion_insights(self, user_id, days=7):
        """Get emotion insights and patterns for user"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            emotions = EmotionLog.query.filter(
                EmotionLog.user_id == user_id,
                EmotionLog.timestamp >= start_date
            ).all()
            
            if not emotions:
                return {'message': 'Not enough data yet, keep using the app!'}
            
            # Analyze patterns
            insights = {
                'dominant_emotion': self._get_dominant_emotion(emotions),
                'emotion_trend': self._calculate_emotion_trend(emotions),
                'best_times': self._find_best_emotional_times(emotions),
                'recommendations': self._generate_recommendations(emotions),
                'pet_impact': self._analyze_pet_impact(user_id, emotions)
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Insights generation error: {e}")
            return {'error': 'Unable to generate insights'}
    
    def _convert_to_child_emotion(self, emotions):
        """Convert technical emotions to child-friendly format"""
        emotion_map = {
            'joy': 'happy',
            'happiness': 'happy',
            'sadness': 'sad',
            'anger': 'frustrated',
            'fear': 'worried',
            'surprise': 'excited',
            'disgust': 'frustrated'
        }
        
        # Get highest scoring emotion
        top_emotion = max(emotions, key=lambda x: x['score'])
        emotion_name = emotion_map.get(top_emotion['label'].lower(), 'calm')
        
        return {
            'emotion': emotion_name,
            'confidence': top_emotion['score'],
            'emoji': self.child_emotions[emotion_name]['emoji'],
            'color': self.child_emotions[emotion_name]['color'],
            'level': self.child_emotions[emotion_name]['level'],
            'timestamp': datetime.now().isoformat()
        }
    
    def _store_emotion_data(self, user_id, input_data, emotion_result, data_type):
        """Store emotion data for learning and analysis"""
        try:
            emotion_log = EmotionLog(
                user_id=user_id,
                emotion=emotion_result['emotion'],
                confidence=emotion_result['confidence'],
                data_type=data_type,
                input_data=json.dumps(input_data) if isinstance(input_data, dict) else str(input_data),
                timestamp=datetime.now()
            )
            
            db.session.add(emotion_log)
            db.session.commit()
            
            # Add to learning buffer
            if user_id not in self.learning_buffer:
                self.learning_buffer[user_id] = []
            
            self.learning_buffer[user_id].append({
                'input': input_data,
                'output': emotion_result,
                'type': data_type,
                'timestamp': datetime.now()
            })
            
        except Exception as e:
            self.logger.error(f"Emotion storage error: {e}")
    
    def _generate_support_response(self, emotion, age, recent_emotions, context):
        """Generate age-appropriate emotional support response"""
        responses = {
            'happy': {
                'young': [
                    "Wow! You're sparkling with happiness! ✨ Your pet is doing a happy dance too!",
                    "What a sunshine day for you! 🌞 Keep spreading those happy vibes!"
                ],
                'older': [
                    "Your happiness is contagious! 😊 What made your day so special?",
                    "It's wonderful to see you so joyful! Your achievements are paying off!"
                ]
            },
            'sad': {
                'young': [
                    "It's okay to feel blue sometimes, little star. 💙 Your pet wants to give you a big hug!",
                    "Even the brightest stars have cloudy days. Let's find something fun to do together!"
                ],
                'older': [
                    "I understand you're feeling down. Remember, every feeling is temporary and valid.",
                    "Your pet companion is here for you. Sometimes talking helps - I'm listening."
                ]
            },
            'worried': {
                'young': [
                    "When I feel worried, I take three magic breaths with my pet. Want to try? 🌬️",
                    "Your brave pet believes in you! You're stronger than your worries."
                ],
                'older': [
                    "Worry shows you care. Let's break down what's bothering you into smaller pieces.",
                    "Your pet companion has some calming activities. Would you like to try one?"
                ]
            }
        }
        
        age_group = 'young' if age < 10 else 'older'
        emotion_responses = responses.get(emotion, responses['happy'])
        
        import random
        message = random.choice(emotion_responses[age_group])
        
        return {
            'message': message,
            'activities': self._get_emotion_activities(emotion),
            'breathing_exercise': self._get_breathing_exercise(emotion),
            'affirmation': self._get_affirmation(emotion, age)
        }
    
    def _get_emotion_activities(self, emotion):
        """Get activities to help with specific emotions"""
        activities = {
            'happy': ['Dance party with your pet!', 'Create a celebration drawing', 'Share your joy story'],
            'sad': ['Pet cuddle time', 'Draw your feelings', 'Listen to gentle music'],
            'worried': ['Breathing exercises', 'Pet meditation', 'Write in worry journal'],
            'frustrated': ['Pet playground time', 'Squeeze stress ball', 'Count to 10 with pet'],
            'excited': ['Channel energy into learning', 'Pet adventure game', 'Create something new']
        }
        
        return activities.get(emotion, activities['happy'])
    
    def _get_breathing_exercise(self, emotion):
        """Get breathing exercise for emotion regulation"""
        exercises = {
            'worried': 'Breathe in for 4, hold for 4, out for 6. Imagine your pet breathing with you.',
            'frustrated': 'Take 5 deep breaths. Picture yourself and your pet in a peaceful garden.',
            'sad': 'Gentle breathing. In through nose, out through mouth. Your pet is right beside you.',
            'excited': 'Calm breathing to focus your energy. In for 3, out for 3.'
        }
        
        return exercises.get(emotion, 'Take three deep, calming breaths with your pet companion.')
    
    def _get_affirmation(self, emotion, age):
        """Get age-appropriate affirmation"""
        if age < 8:
            affirmations = {
                'happy': "I am a bright, shining star! ⭐",
                'sad': "I am loved and I am brave! 💕",
                'worried': "I am safe and I can handle this! 🛡️",
                'frustrated': "I am learning and growing stronger! 💪"
            }
        else:
            affirmations = {
                'happy': "I choose to celebrate my achievements and spread positivity! 🌟",
                'sad': "My feelings are valid, and I have the strength to overcome challenges! 💙",
                'worried': "I am capable and have tools to manage my concerns! 🧠",
                'frustrated': "I can learn from this experience and find solutions! 🎯"
            }
        
        return affirmations.get(emotion, "I am amazing just as I am! ✨")
    
    def _get_default_emotion(self):
        """Return default calm emotion state"""
        return {
            'emotion': 'calm',
            'confidence': 0.5,
            'emoji': '😌',
            'color': '#87CEEB',
            'level': 'peaceful',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_pet_support_message(self, emotion, pet_type):
        """Get pet-specific support message"""
        pet_messages = {
            'dragon': {
                'sad': "Your dragon wraps you in warm, gentle flames of comfort 🔥💙",
                'worried': "Your brave dragon stands guard - you're protected! 🐉🛡️",
                'happy': "Your dragon roars with joy and does aerial flips! 🐉✨"
            },
            'unicorn': {
                'sad': "Your unicorn nuzzles you with magical healing energy 🦄💖",
                'worried': "Your unicorn's horn glows with protective light! 🦄⭐",
                'happy': "Your unicorn gallops through rainbow clouds with you! 🦄🌈"
            },
            'phoenix': {
                'sad': "Your phoenix sings a soothing melody of renewal 🔥🎵",
                'worried': "Your phoenix reminds you: from ashes comes strength! 🔥💪",
                'happy': "Your phoenix soars with flames of celebration! 🔥🎉"
            }
        }
        
        return pet_messages.get(pet_type, {}).get(emotion, 
            f"Your {pet_type} is right here with you, sending love! 💕")
    
    def get_mood_tracking_game(self, user_id):
        """Generate interactive mood tracking game"""
        return {
            'type': 'emotion_garden',
            'description': 'Plant flowers that match your feelings!',
            'instructions': 'Choose the flower that represents how you feel right now',
            'options': [
                {'emotion': 'happy', 'flower': '🌻', 'description': 'Bright Sunflower'},
                {'emotion': 'calm', 'flower': '🌸', 'description': 'Peaceful Cherry Blossom'},
                {'emotion': 'excited', 'flower': '🌺', 'description': 'Vibrant Hibiscus'},
                {'emotion': 'sad', 'flower': '💙', 'description': 'Blue Forget-Me-Not'},
                {'emotion': 'worried', 'flower': '🟣', 'description': 'Purple Lavender'},
                {'emotion': 'frustrated', 'flower': '🔥', 'description': 'Fiery Marigold'}
            ],
            'rewards': {
                'points': 10,
                'badge': 'Emotion Gardner',
                'pet_happiness': 5
            }
        }