"""
Pet AI Service - Advanced Pet Intelligence & Personality System
Provides real-time AI-driven pet behavior, emotions, and interactions
"""

import random
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import tensorflow as tf
from transformers import pipeline, AutoTokenizer, AutoModel
import sqlite3
from ..models.pet import Pet
from ..models.user import User
from .emotion_ai_services import EmotionAIService
from .realtime_ai_services import RealtimeAIService

class PetAIService:
    def __init__(self):
        self.emotion_service = EmotionAIService()
        self.ai_service = RealtimeAIService()
        
        # Load pre-trained sentiment analysis model
        self.sentiment_pipeline = pipeline("sentiment-analysis", 
                                          model="distilbert-base-uncased-finetuned-sst-2-english")
        
        # Pet personality traits
        self.personality_traits = {
            'playful': {'energy_drain': 0.8, 'happiness_gain': 1.2, 'learning_boost': 1.1},
            'calm': {'energy_drain': 0.5, 'happiness_gain': 0.9, 'learning_boost': 1.3},
            'curious': {'energy_drain': 0.7, 'happiness_gain': 1.0, 'learning_boost': 1.5},
            'protective': {'energy_drain': 0.6, 'happiness_gain': 1.1, 'learning_boost': 1.2},
            'mischievous': {'energy_drain': 0.9, 'happiness_gain': 1.3, 'learning_boost': 1.0}
        }
        
        # Advanced pet responses based on context
        self.contextual_responses = {
            'lesson_completed': {
                'dragon': "🐲 ROAAAAAR! You conquered that lesson like a true dragon master! I'm so proud!",
                'unicorn': "🦄 ✨ Magical work! Your knowledge sparkles brighter than my horn!",
                'phoenix': "🔥 Rising to new heights! Your learning burns bright like my flames!",
                'griffin': "🦅 Soaring through knowledge! Your wisdom takes flight!",
                'pegasus': "🐴 Galloping through lessons! Your mind races like the wind!"
            },
            'struggling': {
                'dragon': "🐲 Hey champion, even dragons need practice! Let's breathe some fire into this together!",
                'unicorn': "🦄 Don't worry, every magical journey has bumps! I believe in your inner sparkle!",
                'phoenix': "🔥 From ashes we rise! Every mistake is a chance to burn brighter!",
                'griffin': "🦅 Strong wings need practice! Let's soar through this challenge together!",
                'pegasus': "🐴 Steady gallop wins the race! We'll master this step by step!"
            },
            'achievement_unlocked': {
                'dragon': "🐲 LEGENDARY! You've unlocked the ancient power of knowledge!",
                'unicorn': "🦄 ✨ Pure magic! Your achievement shines across the realm!",
                'phoenix': "🔥 BLAZING SUCCESS! You've risen to legendary status!",
                'griffin': "🦅 MAJESTIC! Your achievement echoes through the skies!",
                'pegasus': "🐴 GALLOPING GLORY! You've reached the finish line in style!"
            }
        }
        
        # Initialize neural network for pet behavior prediction
        self.behavior_model = self._build_behavior_model()
        
    def _build_behavior_model(self):
        """Build neural network for predicting pet behavior"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(10,)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(5, activation='softmax')  # 5 behavior states
        ])
        
        model.compile(optimizer='adam',
                     loss='categorical_crossentropy',
                     metrics=['accuracy'])
        return model
    
    def analyze_child_interaction(self, user_id: int, interaction_data: Dict) -> Dict:
        """Analyze child's interaction patterns and adjust pet behavior"""
        
        # Get user's emotional state
        emotion_data = self.emotion_service.analyze_user_emotion(user_id)
        
        # Extract interaction features
        features = self._extract_interaction_features(interaction_data, emotion_data)
        
        # Predict optimal pet behavior
        behavior_prediction = self.behavior_model.predict(np.array([features]))
        behavior_type = self._interpret_behavior_prediction(behavior_prediction[0])
        
        # Generate personalized pet response
        pet_response = self._generate_contextual_response(
            interaction_data.get('pet_type', 'dragon'),
            behavior_type,
            interaction_data.get('context', 'general')
        )
        
        return {
            'behavior_type': behavior_type,
            'response': pet_response,
            'emotion_detected': emotion_data.get('primary_emotion', 'neutral'),
            'engagement_level': self._calculate_engagement_level(features),
            'learning_recommendation': self._generate_learning_recommendation(features, behavior_type)
        }
    
    def _extract_interaction_features(self, interaction_data: Dict, emotion_data: Dict) -> List[float]:
        """Extract numerical features from interaction data"""
        features = [
            interaction_data.get('session_duration', 0) / 3600,  # Hours
            interaction_data.get('clicks_per_minute', 0),
            interaction_data.get('correct_answers_ratio', 0),
            interaction_data.get('time_on_task', 0) / 60,  # Minutes
            emotion_data.get('happiness_score', 0.5),
            emotion_data.get('frustration_score', 0),
            emotion_data.get('engagement_score', 0.5),
            interaction_data.get('help_requests', 0),
            interaction_data.get('achievement_unlocked', 0),
            interaction_data.get('social_interactions', 0)
        ]
        return features
    
    def _interpret_behavior_prediction(self, prediction: np.ndarray) -> str:
        """Convert neural network output to behavior type"""
        behaviors = ['encouraging', 'playful', 'calm', 'supportive', 'celebratory']
        return behaviors[np.argmax(prediction)]
    
    def _generate_contextual_response(self, pet_type: str, behavior_type: str, context: str) -> str:
        """Generate contextual pet response based on AI analysis"""
        
        base_responses = self.contextual_responses.get(context, {})
        pet_response = base_responses.get(pet_type, "")
        
        if not pet_response:
            # Generate dynamic response using AI
            prompt = f"Generate a {behavior_type} response from a {pet_type} pet to a child in context: {context}"
            pet_response = self.ai_service.generate_response(prompt, max_length=50)
        
        # Add behavioral modifiers
        if behavior_type == 'encouraging':
            pet_response += " 💪 You've got this, champion!"
        elif behavior_type == 'playful':
            pet_response += " 🎮 Want to play a quick game to celebrate?"
        elif behavior_type == 'calm':
            pet_response += " 🌸 Take a deep breath, we'll go at your pace."
        elif behavior_type == 'supportive':
            pet_response += " 🤗 I'm right here with you, always!"
        elif behavior_type == 'celebratory':
            pet_response += " 🎉 Time for a victory dance!"
        
        return pet_response
    
    def _calculate_engagement_level(self, features: List[float]) -> float:
        """Calculate child's engagement level from interaction features"""
        # Weighted combination of key engagement indicators
        weights = [0.2, 0.25, 0.3, 0.15, 0.1]  # Corresponding to key features
        engagement_features = features[:5]  # Use first 5 features
        
        engagement_score = sum(w * f for w, f in zip(weights, engagement_features))
        return min(max(engagement_score, 0), 1)  # Clamp between 0 and 1
    
    def _generate_learning_recommendation(self, features: List[float], behavior_type: str) -> Dict:
        """Generate personalized learning recommendations"""
        
        engagement_level = self._calculate_engagement_level(features)
        correct_answers_ratio = features[2]
        
        recommendations = {
            'difficulty_adjustment': 'maintain',
            'activity_type': 'current',
            'break_suggestion': False,
            'social_interaction': False
        }
        
        # Adjust difficulty based on performance
        if correct_answers_ratio < 0.3:
            recommendations['difficulty_adjustment'] = 'decrease'
            recommendations['activity_type'] = 'review'
        elif correct_answers_ratio > 0.8:
            recommendations['difficulty_adjustment'] = 'increase'
            recommendations['activity_type'] = 'challenge'
        
        # Suggest breaks for low engagement
        if engagement_level < 0.4:
            recommendations['break_suggestion'] = True
            recommendations['activity_type'] = 'game'
        
        # Encourage social interaction for isolated users
        if features[9] < 0.1:  # Low social interactions
            recommendations['social_interaction'] = True
        
        return recommendations
    
    def update_pet_personality(self, pet_id: int, interaction_history: List[Dict]) -> Dict:
        """Update pet personality based on long-term interaction patterns"""
        
        # Analyze interaction patterns over time
        personality_scores = {trait: 0 for trait in self.personality_traits.keys()}
        
        for interaction in interaction_history:
            # Analyze interaction type and update personality scores
            interaction_type = interaction.get('type', 'general')
            user_emotion = interaction.get('user_emotion', 'neutral')
            
            if interaction_type == 'learning' and user_emotion == 'frustrated':
                personality_scores['calm'] += 1
                personality_scores['protective'] += 1
            elif interaction_type == 'achievement' and user_emotion == 'happy':
                personality_scores['playful'] += 1
                personality_scores['curious'] += 1
            elif interaction_type == 'exploration':
                personality_scores['curious'] += 2
            elif interaction_type == 'social':
                personality_scores['playful'] += 1
        
        # Determine dominant personality trait
        dominant_trait = max(personality_scores, key=personality_scores.get)
        
        # Update pet in database
        with sqlite3.connect('app.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE pets SET personality_trait = ?, 
                personality_strength = ? WHERE id = ?
            ''', (dominant_trait, personality_scores[dominant_trait], pet_id))
            conn.commit()
        
        return {
            'dominant_trait': dominant_trait,
            'trait_scores': personality_scores,
            'behavior_modifiers': self.personality_traits[dominant_trait]
        }
    
    def generate_pet_dream(self, pet_id: int, user_achievements: List[str]) -> Dict:
        """Generate a personalized dream sequence for the pet based on user progress"""
        
        pet = Pet.query.get(pet_id)
        if not pet:
            return {"error": "Pet not found"}
        
        # Create dream narrative based on achievements
        dream_elements = []
        for achievement in user_achievements:
            if 'math' in achievement.lower():
                dream_elements.append("floating through clouds of numbers")
            elif 'reading' in achievement.lower():
                dream_elements.append("dancing with magical story characters")
            elif 'science' in achievement.lower():
                dream_elements.append("exploring galaxies and discovering new worlds")
            elif 'art' in achievement.lower():
                dream_elements.append("painting rainbows across dream skies")
        
        if not dream_elements:
            dream_elements = ["playing in fields of golden sunlight"]
        
        dream_narrative = f"Last night, {pet.name} dreamed of " + ", ".join(dream_elements) + "."
        
        # Generate AI-enhanced dream story
        enhanced_dream = self.ai_service.enhance_story(
            dream_narrative, 
            style="whimsical children's story",
            length="short"
        )
        
        return {
            'dream_title': f"{pet.name}'s Magical Dream",
            'dream_story': enhanced_dream,
            'dream_image_prompt': f"whimsical dream scene with {pet.pet_type} " + " and ".join(dream_elements),
            'emotional_tone': 'magical and inspiring'
        }
    
    def calculate_pet_evolution(self, pet_id: int, user_progress: Dict) -> Dict:
        """Calculate if pet should evolve based on user progress and care"""
        
        pet = Pet.query.get(pet_id)
        if not pet:
            return {"error": "Pet not found"}
        
        evolution_score = 0
        evolution_requirements = {
            'happiness_threshold': 80,
            'health_threshold': 75,
            'learning_milestones': 5,
            'days_together': 7,
            'care_consistency': 0.8
        }
        
        # Check evolution criteria
        if pet.happiness >= evolution_requirements['happiness_threshold']:
            evolution_score += 25
        
        if pet.health >= evolution_requirements['health_threshold']:
            evolution_score += 25
        
        learning_milestones = user_progress.get('completed_lessons', 0)
        if learning_milestones >= evolution_requirements['learning_milestones']:
            evolution_score += 25
        
        days_together = (datetime.now() - pet.created_at).days
        if days_together >= evolution_requirements['days_together']:
            evolution_score += 25
        
        can_evolve = evolution_score >= 75
        
        if can_evolve:
            # Generate evolution options
            current_type = pet.pet_type
            evolution_options = self._get_evolution_options(current_type)
            
            return {
                'can_evolve': True,
                'evolution_score': evolution_score,
                'evolution_options': evolution_options,
                'celebration_message': f"🌟 {pet.name} is ready to evolve! Your love and care have unlocked new possibilities!"
            }
        else:
            missing_requirements = []
            if pet.happiness < evolution_requirements['happiness_threshold']:
                missing_requirements.append(f"Happiness: {pet.happiness}/{evolution_requirements['happiness_threshold']}")
            if pet.health < evolution_requirements['health_threshold']:
                missing_requirements.append(f"Health: {pet.health}/{evolution_requirements['health_threshold']}")
            if learning_milestones < evolution_requirements['learning_milestones']:
                missing_requirements.append(f"Learning: {learning_milestones}/{evolution_requirements['learning_milestones']}")
            if days_together < evolution_requirements['days_together']:
                missing_requirements.append(f"Days together: {days_together}/{evolution_requirements['days_together']}")
            
            return {
                'can_evolve': False,
                'evolution_score': evolution_score,
                'missing_requirements': missing_requirements,
                'encouragement_message': f"Keep caring for {pet.name}! You're {evolution_score}% there!"
            }
    
    def _get_evolution_options(self, current_type: str) -> List[Dict]:
        """Get possible evolution forms for a pet type"""
        evolution_tree = {
            'dragon': [
                {'type': 'ancient_dragon', 'name': 'Ancient Dragon', 'description': 'Wise guardian of all knowledge'},
                {'type': 'crystal_dragon', 'name': 'Crystal Dragon', 'description': 'Sparkles with pure learning energy'},
                {'type': 'rainbow_dragon', 'name': 'Rainbow Dragon', 'description': 'Breathes colors of creativity'}
            ],
            'unicorn': [
                {'type': 'alicorn', 'name': 'Alicorn', 'description': 'Magical winged unicorn of wisdom'},
                {'type': 'star_unicorn', 'name': 'Star Unicorn', 'description': 'Celestial guide through learning'},
                {'type': 'moon_unicorn', 'name': 'Moon Unicorn', 'description': 'Dreams come true with this companion'}
            ],
            'phoenix': [
                {'type': 'golden_phoenix', 'name': 'Golden Phoenix', 'description': 'Soars through knowledge with golden wings'},
                {'type': 'ice_phoenix', 'name': 'Ice Phoenix', 'description': 'Cool and calm master of focus'},
                {'type': 'thunder_phoenix', 'name': 'Thunder Phoenix', 'description': 'Strikes through challenges with power'}
            ]
        }
        
        return evolution_tree.get(current_type, [
            {'type': f'evolved_{current_type}', 'name': f'Evolved {current_type.title()}', 'description': 'A more powerful version of your beloved companion'}
        ])
    
    def train_behavior_model(self, training_data: List[Dict]) -> Dict:
        """Train the pet behavior model with real user interaction data"""
        
        if len(training_data) < 100:
            return {"error": "Insufficient training data", "required": 100, "provided": len(training_data)}
        
        # Prepare training data
        X = []
        y = []
        
        behavior_to_index = {
            'encouraging': [1, 0, 0, 0, 0],
            'playful': [0, 1, 0, 0, 0],
            'calm': [0, 0, 1, 0, 0],
            'supportive': [0, 0, 0, 1, 0],
            'celebratory': [0, 0, 0, 0, 1]
        }
        
        for data_point in training_data:
            features = self._extract_interaction_features(
                data_point.get('interaction', {}),
                data_point.get('emotion', {})
            )
            behavior = data_point.get('optimal_behavior', 'encouraging')
            
            X.append(features)
            y.append(behavior_to_index.get(behavior, behavior_to_index['encouraging']))
        
        X = np.array(X)
        y = np.array(y)
        
        # Train the model
        history = self.behavior_model.fit(
            X, y,
            epochs=50,
            batch_size=32,
            validation_split=0.2,
            verbose=0
        )
        
        # Save the trained model
        self.behavior_model.save('app/models/saved_models/pet_behavior_model.h5')
        
        return {
            'training_completed': True,
            'final_accuracy': history.history['accuracy'][-1],
            'final_loss': history.history['loss'][-1],
            'training_samples': len(training_data),
            'model_saved': True
        }