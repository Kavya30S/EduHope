import json
import numpy as np
import torch
import torch.nn as nn
from datetime import datetime, timedelta
from transformers import GPT2LMHeadModel, GPT2Tokenizer, Trainer, TrainingArguments
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
from threading import Thread, Lock
import asyncio
from collections import deque, defaultdict
import logging

class RealtimeAIService:
    def __init__(self):
        """Initialize real-time AI learning service for personalized education"""
        self.logger = logging.getLogger(__name__)
        
        # Load base models
        self.tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.base_model = GPT2LMHeadModel.from_pretrained('gpt2')
        
        # User-specific models and data
        self.user_models = {}
        self.user_data = {}
        self.learning_queues = defaultdict(deque)
        self.model_lock = Lock()
        
        # Real-time learning parameters
        self.batch_size = 8
        self.learning_rate = 1e-5
        self.max_interactions = 1000
        self.retrain_threshold = 50
        
        # Child learning preferences tracking
        self.learning_styles = {
            'visual': {'weight': 1.0, 'content_types': ['images', 'diagrams', 'colors']},
            'auditory': {'weight': 1.0, 'content_types': ['sounds', 'music', 'speech']},
            'kinesthetic': {'weight': 1.0, 'content_types': ['games', 'activities', 'movement']},
            'reading': {'weight': 1.0, 'content_types': ['text', 'stories', 'words']}
        }
        
        # Subject difficulty adaptation
        self.subject_weights = {
            'math': 1.0,
            'language': 1.0,  
            'science': 1.0,
            'history': 1.0,
            'art': 1.0,
            'music': 1.0
        }
        
        # Start background learning thread
        self.learning_thread = Thread(target=self._continuous_learning_loop, daemon=True)
        self.learning_thread.start()
        
    def initialize_user_model(self, user_id, user_profile):
        """Initialize personalized AI model for new user"""
        try:
            with self.model_lock:
                if user_id not in self.user_models:
                    # Clone base model for user
                    user_model = GPT2LMHeadModel.from_pretrained('gpt2')
                    
                    # Initialize user-specific data
                    self.user_models[user_id] = {
                        'model': user_model,
                        'tokenizer': self.tokenizer,
                        'performance_history': [],
                        'learning_style_weights': self.learning_styles.copy(),
                        'subject_mastery': self.subject_weights.copy(),
                        'interaction_count': 0,
                        'last_updated': datetime.now(),
                        'difficulty_level': self._calculate_initial_difficulty(user_profile)
                    }
                    
                    self.user_data[user_id] = {
                        'preferences': user_profile,
                        'interaction_history': deque(maxlen=self.max_interactions),
                        'performance_metrics': defaultdict(list),
                        'learning_path': [],
                        'strengths': [],
                        'improvement_areas': []
                    }
                    
                    self.logger.info(f"Initialized personalized AI model for user {user_id}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Adaptation error: {e}")
            return {'type': 'no_change'}
    
    def _generate_personalized_response(self, user_id, interaction_data):
        """Generate personalized response using user's model"""
        try:
            user_model_data = self.user_models[user_id]
            user_profile = self.user_data[user_id]
            
            # Create context prompt
            context = self._build_context_prompt(user_id, interaction_data)
            
            # Generate using personalized model
            inputs = self.tokenizer.encode(context, return_tensors='pt', truncate=True, max_length=512)
            
            with torch.no_grad():
                outputs = user_model_data['model'].generate(
                    inputs,
                    max_length=inputs.shape[1] + 100,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
            
            # Make child-friendly and add personality
            response = self._add_personality_to_response(user_id, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Response generation error: {e}")
            return "That's interesting! Let's explore this together! 🌟"
    
    def _generate_adaptive_content(self, model, content_type, subject, difficulty, learning_style, preferences):
        """Generate content adapted to user's learning style and level"""
        
        style_prompts = {
            'visual': "Create colorful, image-rich content with diagrams and visual elements.",
            'auditory': "Include songs, rhymes, and sound-based learning elements.",
            'kinesthetic': "Design hands-on activities and movement-based learning.",
            'reading': "Use stories and text-based explanations with rich vocabulary."
        }
        
        difficulty_adjustments = {
            0.3: "very simple, basic concepts",
            0.5: "beginner level with clear explanations", 
            0.7: "intermediate level with some challenge",
            1.0: "standard level",
            1.5: "advanced concepts",
            2.0: "expert level with complex ideas"
        }
        
        age = preferences.get('age', 8)
        interests = preferences.get('interests', ['animals', 'games'])
        
        prompt = f"""
        Create {content_type} for {subject} at {difficulty_adjustments.get(difficulty, 'standard')} level.
        Learning style: {style_prompts.get(learning_style, 'mixed approach')}.
        Age: {age} years old.
        Interests: {', '.join(interests)}.
        Make it engaging, fun, and include magical elements with fantasy creatures.
        """
        
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors='pt', truncate=True, max_length=400)
            
            with torch.no_grad():
                outputs = model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 200,
                    temperature=0.8,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            content = self.tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
            
            return self._structure_content(content, content_type, subject)
            
        except Exception as e:
            self.logger.error(f"Adaptive content generation error: {e}")
            return self._generate_fallback_content(content_type, subject, difficulty)
    
    def _make_child_friendly(self, content, age):
        """Make content appropriate and engaging for children"""
        
        # Add age-appropriate language
        if age < 6:
            # Very simple language
            content = content.replace("difficult", "tricky")
            content = content.replace("complex", "big")
            content = content.replace("analyze", "look at")
        elif age < 10:
            # Elementary level
            content = content.replace("subsequently", "then")
            content = content.replace("furthermore", "also")
            content = content.replace("consequently", "so")
        
        # Add magical elements
        magical_replacements = {
            "lesson": "magical quest",
            "exercise": "adventure challenge", 
            "problem": "puzzle mystery",
            "answer": "magic solution",
            "study": "explore",
            "learn": "discover"
        }
        
        for old, new in magical_replacements.items():
            content = content.replace(old, new)
        
        # Add encouraging phrases
        encouragements = [
            "You're doing amazingly! ✨",
            "What a brilliant explorer you are! 🌟", 
            "Your brain is growing stronger! 💪",
            "Magic is happening in your mind! 🧙‍♀️"
        ]
        
        import random
        if len(content) > 100:
            content += f" {random.choice(encouragements)}"
        
        return content
    
    def _continuous_learning_loop(self):
        """Background thread for continuous model improvement"""
        while True:
            try:
                for user_id in list(self.learning_queues.keys()):
                    if len(self.learning_queues[user_id]) >= self.retrain_threshold:
                        self._perform_incremental_training(user_id)
                
                # Sleep for 30 seconds before next check
                asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Continuous learning error: {e}")
                asyncio.sleep(60)  # Wait longer on error
    
    def _perform_incremental_training(self, user_id):
        """Perform incremental training on user's model"""
        try:
            with self.model_lock:
                if user_id not in self.user_models:
                    return
                
                # Get training data
                training_data = list(self.learning_queues[user_id])
                self.learning_queues[user_id].clear()
                
                # Prepare training dataset
                dataset = self._prepare_training_dataset(training_data)
                
                if len(dataset) < 5:  # Need minimum data
                    return
                
                # Setup training
                training_args = TrainingArguments(
                    output_dir=f"./models/user_{user_id}",
                    num_train_epochs=1,
                    per_device_train_batch_size=2,
                    learning_rate=self.learning_rate,
                    logging_steps=10,
                    save_steps=50,
                    evaluation_strategy="no",
                    save_total_limit=1
                )
                
                # Create trainer
                trainer = Trainer(
                    model=self.user_models[user_id]['model'],
                    args=training_args,
                    train_dataset=dataset,
                    tokenizer=self.tokenizer
                )
                
                # Train model
                trainer.train()
                
                # Update last training time
                self.user_models[user_id]['last_updated'] = datetime.now()
                
                self.logger.info(f"Incremental training completed for user {user_id}")
                
        except Exception as e:
            self.logger.error(f"Incremental training error: {e}")
    
    def _analyze_strengths_weaknesses(self, user_id):
        """Analyze user's learning strengths and weaknesses"""
        try:
            performance_data = self.user_data[user_id]['performance_metrics']
            
            strengths = {}
            weaknesses = {}
            
            for subject, metrics in performance_data.items():
                if not metrics:
                    continue
                
                # Calculate average performance
                recent_metrics = metrics[-10:]  # Last 10 interactions
                avg_accuracy = np.mean([m['performance']['accuracy'] for m in recent_metrics])
                avg_speed = np.mean([m['performance'].get('response_time', 10) for m in recent_metrics])
                
                # Classify as strength or weakness
                if avg_accuracy > 0.8 and avg_speed < 15:
                    strengths[subject] = avg_accuracy
                elif avg_accuracy < 0.6 or avg_speed > 30:
                    weaknesses[subject] = avg_accuracy
            
            return strengths, weaknesses
            
        except Exception as e:
            self.logger.error(f"Strength/weakness analysis error: {e}")
            return {}, {}
    
    def _generate_subject_path(self, user_id, subject, mastery_level, path_type):
        """Generate learning path for specific subject"""
        
        base_topics = {
            'math': ['counting', 'addition', 'subtraction', 'multiplication', 'division', 'fractions'],
            'language': ['phonics', 'vocabulary', 'grammar', 'reading', 'writing', 'storytelling'],
            'science': ['animals', 'plants', 'weather', 'space', 'experiments', 'nature'],
            'history': ['ancient times', 'explorers', 'inventions', 'cultures', 'heroes', 'timeline'],
            'art': ['colors', 'shapes', 'drawing', 'painting', 'crafts', 'creativity'],
            'music': ['rhythm', 'melody', 'instruments', 'songs', 'composition', 'listening']
        }
        
        topics = base_topics.get(subject, ['basics', 'intermediate', 'advanced'])
        
        path_items = []
        
        if path_type == 'remedial':
            # Start with easier topics
            difficulty_progression = [0.3, 0.4, 0.5, 0.6]
            topics_to_use = topics[:4]  # First 4 topics
        else:
            # Advanced path
            difficulty_progression = [1.0, 1.2, 1.5, 1.8]
            topics_to_use = topics[-4:]  # Last 4 topics
        
        for i, topic in enumerate(topics_to_use):
            difficulty = difficulty_progression[i] if i < len(difficulty_progression) else 1.0
            
            path_items.append({
                'subject': subject,
                'topic': topic,
                'difficulty': difficulty,
                'estimated_time': 15 + (difficulty * 10),
                'type': self._get_preferred_content_type(user_id),
                'rewards': {
                    'points': int(20 * difficulty),
                    'pet_food': int(5 * difficulty),
                    'accessories': difficulty > 1.0
                }
            })
        
        return path_items
    
    def _add_engaging_elements(self, user_id, learning_path):
        """Add fun and engaging elements to learning path"""
        
        user_profile = self.user_data[user_id]
        interests = user_profile['preferences'].get('interests', [])
        
        # Add themed quests based on interests
        if 'animals' in interests:
            learning_path.insert(2, {
                'type': 'animal_quest',
                'description': 'Help magical animals solve problems!',
                'duration': 20,
                'rewards': {'pet_happiness': 15, 'badge': 'Animal Friend'}
            })
        
        if 'space' in interests:
            learning_path.insert(4, {
                'type': 'space_adventure',
                'description': 'Journey through the galaxy of knowledge!',
                'duration': 25,
                'rewards': {'pet_food': 10, 'badge': 'Space Explorer'}
            })
        
        # Add mini-games every few lessons
        for i in range(3, len(learning_path), 4):
            learning_path.insert(i, {
                'type': 'mini_game',
                'description': 'Play with your pet companion!',
                'duration': 10,
                'rewards': {'pet_happiness': 20, 'points': 50}
            })
        
        return learning_path
    
    def get_real_time_feedback(self, user_id, current_activity):
        """Provide real-time feedback during learning activities"""
        try:
            if user_id not in self.user_models:
                return self._get_generic_feedback()
            
            user_model = self.user_models[user_id]
            performance_history = self.user_data[user_id]['performance_metrics']
            
            # Analyze current performance
            current_subject = current_activity.get('subject', 'general')
            current_accuracy = current_activity.get('accuracy', 0)
            current_time = current_activity.get('time_spent', 0)
            
            # Generate adaptive feedback
            feedback = self._generate_adaptive_feedback(
                user_id, current_subject, current_accuracy, current_time
            )
            
            # Add pet companion reactions
            if 'pet' in self.user_data[user_id]['preferences']:
                pet_reaction = self._get_pet_reaction(current_accuracy)
                feedback['pet_reaction'] = pet_reaction
            
            # Suggest next steps
            feedback['next_suggestion'] = self._get_next_step_suggestion(
                user_id, current_activity
            )
            
            return feedback
            
        except Exception as e:
            self.logger.error(f"Real-time feedback error: {e}")
            return self._get_generic_feedback()
    
    def _get_generic_feedback(self):
        """Fallback feedback when personalized feedback fails"""
        return {
            'message': "You're doing great! Keep exploring! 🌟",
            'encouragement': "Every step forward is progress! 💪",
            'suggestion': "Try the next challenge when you're ready!"
        } as e:
            self.logger.error(f"User model initialization error: {e}")
            return False
    
    def process_user_interaction(self, user_id, interaction_data):
        """Process and learn from user interaction in real-time"""
        try:
            if user_id not in self.user_models:
                return {'error': 'User model not initialized'}
            
            # Extract interaction features
            interaction_features = self._extract_interaction_features(interaction_data)
            
            # Update user data
            self.user_data[user_id]['interaction_history'].append({
                'timestamp': datetime.now(),
                'data': interaction_data,
                'features': interaction_features
            })
            
            # Real-time adaptation
            adaptation_result = self._adapt_to_interaction(user_id, interaction_features)
            
            # Queue for batch learning
            self.learning_queues[user_id].append(interaction_features)
            
            # Generate personalized response
            response = self._generate_personalized_response(user_id, interaction_data)
            
            # Update model if threshold reached
            if len(self.learning_queues[user_id]) >= self.retrain_threshold:
                self._schedule_model_update(user_id)
            
            return {
                'response': response,
                'adaptation': adaptation_result,
                'learning_progress': self._get_learning_progress(user_id),
                'recommendations': self._get_next_recommendations(user_id)
            }
            
        except Exception as e:
            self.logger.error(f"Interaction processing error: {e}")
            return {'error': 'Processing failed'}
    
    def generate_personalized_content(self, user_id, content_type, subject, difficulty=None):
        """Generate personalized educational content based on user's learning profile"""
        try:
            if user_id not in self.user_models:
                return self._generate_generic_content(content_type, subject)
            
            user_model_data = self.user_models[user_id]
            user_profile = self.user_data[user_id]
            
            # Determine optimal difficulty
            if difficulty is None:
                difficulty = self._calculate_optimal_difficulty(user_id, subject)
            
            # Adapt to learning style
            learning_style = self._get_dominant_learning_style(user_id)
            
            # Generate content using personalized model
            content = self._generate_adaptive_content(
                user_model_data['model'],
                content_type,
                subject,
                difficulty,
                learning_style,
                user_profile['preferences']
            )
            
            # Add child-friendly elements
            content = self._make_child_friendly(content, user_profile['preferences'].get('age', 8))
            
            # Track content generation for learning
            self._track_content_usage(user_id, content_type, subject, difficulty)
            
            return content
            
        except Exception as e:
            self.logger.error(f"Content generation error: {e}")
            return self._generate_generic_content(content_type, subject)
    
    def update_learning_progress(self, user_id, lesson_data, performance_data):
        """Update user's learning progress and adapt model"""
        try:
            if user_id not in self.user_models:
                return False
            
            # Process performance data
            performance_metrics = self._analyze_performance(performance_data)
            
            # Update mastery levels
            self._update_subject_mastery(user_id, lesson_data['subject'], performance_metrics)
            
            # Adapt difficulty
            self._adapt_difficulty_level(user_id, lesson_data['subject'], performance_metrics)
            
            # Update learning style preferences
            self._update_learning_style_weights(user_id, lesson_data, performance_metrics)
            
            # Store performance history
            self.user_data[user_id]['performance_metrics'][lesson_data['subject']].append({
                'timestamp': datetime.now(),
                'performance': performance_metrics,
                'lesson_type': lesson_data.get('type', 'general'),
                'difficulty': lesson_data.get('difficulty', 1.0)
            })
            
            # Update interaction count
            self.user_models[user_id]['interaction_count'] += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Learning progress update error: {e}")
            return False
    
    def get_adaptive_learning_path(self, user_id):
        """Generate personalized learning path based on user's progress and preferences"""
        try:
            if user_id not in self.user_models:
                return self._get_default_learning_path()
            
            user_model_data = self.user_models[user_id]
            user_profile = self.user_data[user_id]
            
            # Analyze current strengths and weaknesses
            strengths, weaknesses = self._analyze_strengths_weaknesses(user_id)
            
            # Generate adaptive path
            learning_path = []
            
            # Focus on weak areas with gradual progression
            for subject, mastery_level in weaknesses.items():
                if mastery_level < 0.7:  # Below 70% mastery
                    path_items = self._generate_subject_path(
                        user_id, subject, mastery_level, 'remedial'
                    )
                    learning_path.extend(path_items)
            
            # Reinforce strengths with advanced content
            for subject, mastery_level in strengths.items():
                if mastery_level > 0.8:  # Above 80% mastery
                    path_items = self._generate_subject_path(
                        user_id, subject, mastery_level, 'advanced'
                    )
                    learning_path.extend(path_items)
            
            # Add variety and fun elements
            learning_path = self._add_engaging_elements(user_id, learning_path)
            
            # Store updated path
            self.user_data[user_id]['learning_path'] = learning_path
            
            return {
                'path': learning_path,
                'estimated_duration': self._estimate_path_duration(learning_path),
                'milestones': self._create_milestones(learning_path),
                'rewards': self._plan_rewards(learning_path)
            }
            
        except Exception as e:
            self.logger.error(f"Learning path generation error: {e}")
            return self._get_default_learning_path()
    
    def _extract_interaction_features(self, interaction_data):
        """Extract features from user interaction for learning"""
        features = {
            'response_time': interaction_data.get('response_time', 0),
            'accuracy': interaction_data.get('accuracy', 0),
            'attempt_count': interaction_data.get('attempts', 1),
            'help_requests': interaction_data.get('help_used', 0),
            'engagement_score': interaction_data.get('engagement', 0.5),
            'content_type': interaction_data.get('type', 'general'),
            'subject': interaction_data.get('subject', 'general'),
            'difficulty': interaction_data.get('difficulty', 1.0),
            'emotional_state': interaction_data.get('emotion', 'neutral')
        }
        
        return features
    
    def _adapt_to_interaction(self, user_id, features):
        """Adapt model parameters based on interaction"""
        try:
            user_model = self.user_models[user_id]
            
            # Adapt difficulty based on performance
            if features['accuracy'] > 0.9 and features['response_time'] < 10:
                # Too easy, increase difficulty
                subject = features['subject']
                current_difficulty = user_model['difficulty_level'].get(subject, 1.0)
                user_model['difficulty_level'][subject] = min(2.0, current_difficulty + 0.1)
                adaptation = 'increased_difficulty'
                
            elif features['accuracy'] < 0.5 or features['attempt_count'] > 3:
                # Too hard, decrease difficulty
                subject = features['subject']
                current_difficulty = user_model['difficulty_level'].get(subject, 1.0)
                user_model['difficulty_level'][subject] = max(0.3, current_difficulty - 0.1)
                adaptation = 'decreased_difficulty'
                
            else:
                adaptation = 'maintained_level'
            
            # Adapt learning style weights
            content_type = features['content_type']
            engagement = features['engagement_score']
            
            for style, data in user_model['learning_style_weights'].items():
                if content_type in data['content_types']:
                    # Increase weight for engaging content types
                    data['weight'] = min(2.0, data['weight'] + engagement * 0.1)
                else:
                    # Slightly decrease others to maintain balance
                    data['weight'] = max(0.5, data['weight'] - 0.02)
            
            return {
                'type': adaptation,
                'difficulty_change': user_model['difficulty_level'].get(features['subject'], 1.0),
                'style_weights': {k: v['weight'] for k, v in user_model['learning_style_weights'].items()}
            }
            
        except Exception