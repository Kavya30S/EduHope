import random
import json
from datetime import datetime
from typing import Dict, List, Any
from app.services.realtime_ai_services import RealtimeAIService
from app.services.analytics_service import AnalyticsService

class KnowledgeAssessmentGame:
    """Interactive knowledge assessment through engaging games"""
    
    def __init__(self):
        self.ai_service = RealtimeAIService()
        self.analytics = AnalyticsService()
        
        # Game configuration
        self.games = {
            'math_magic': {
                'name': 'Math Magic Adventure',
                'description': 'Help the magical creatures solve math puzzles!',
                'age_groups': ['3-6', '6-12', '12-18'],
                'subjects': ['math'],
                'duration': 10
            },
            'word_wizard': {
                'name': 'Word Wizard Quest',
                'description': 'Cast spelling spells and build vocabulary!',
                'age_groups': ['6-12', '12-18'],
                'subjects': ['language', 'vocabulary'],
                'duration': 12
            },
            'science_explorer': {
                'name': 'Science Explorer Journey',
                'description': 'Discover amazing scientific facts through experiments!',
                'age_groups': ['6-12', '12-18'],
                'subjects': ['science', 'biology', 'physics'],
                'duration': 15
            },
            'history_hunter': {
                'name': 'History Time Hunter',
                'description': 'Travel through time and discover historical mysteries!',
                'age_groups': ['9-12', '12-18'],
                'subjects': ['history', 'geography'],
                'duration': 12
            },
            'creative_crafter': {
                'name': 'Creative Crafter Challenge',
                'description': 'Express your creativity through art and imagination!',
                'age_groups': ['3-6', '6-12', '12-18'],
                'subjects': ['art', 'creativity', 'music'],
                'duration': 8
            }
        }
        
        # Adaptive difficulty levels
        self.difficulty_levels = {
            1: {'name': 'Sprout', 'description': 'Just beginning to bloom!', 'multiplier': 1.0},
            2: {'name': 'Seedling', 'description': 'Growing stronger!', 'multiplier': 1.2},
            3: {'name': 'Flower', 'description': 'Beautiful and bright!', 'multiplier': 1.5},
            4: {'name': 'Tree', 'description': 'Strong and wise!', 'multiplier': 2.0},
            5: {'name': 'Forest', 'description': 'Master of knowledge!', 'multiplier': 2.5}
        }

    def generate_assessment_session(self, user_id: int, age_group: str, preferences: Dict) -> Dict:
        """Generate a personalized assessment session"""
        
        # Select appropriate games based on age and preferences
        suitable_games = self._select_games_for_user(age_group, preferences)
        
        # Create session structure
        session = {
            'id': f"assess_{user_id}_{int(datetime.now().timestamp())}",
            'user_id': user_id,
            'age_group': age_group,
            'games': suitable_games,
            'current_game': 0,
            'start_time': datetime.now().isoformat(),
            'progress': 0,
            'results': {},
            'adaptive_data': {
                'current_difficulty': 2,  # Start at medium
                'success_streak': 0,
                'failure_streak': 0,
                'learning_style': 'unknown'
            }
        }
        
        return session

    def _select_games_for_user(self, age_group: str, preferences: Dict) -> List[Dict]:
        """Select appropriate games for the user"""
        
        suitable_games = []
        preferred_subjects = preferences.get('subjects', [])
        
        for game_id, game_info in self.games.items():
            if age_group in game_info['age_groups']:
                # Check if game matches user's subject preferences
                if not preferred_subjects or any(subject in game_info['subjects'] for subject in preferred_subjects):
                    suitable_games.append({
                        'id': game_id,
                        'info': game_info,
                        'questions': self._generate_questions_for_game(game_id, age_group)
                    })
        
        # Ensure we have at least 3-5 games
        if len(suitable_games) < 3:
            # Add some general games
            for game_id, game_info in self.games.items():
                if age_group in game_info['age_groups'] and game_id not in [g['id'] for g in suitable_games]:
                    suitable_games.append({
                        'id': game_id,
                        'info': game_info,
                        'questions': self._generate_questions_for_game(game_id, age_group)
                    })
                    if len(suitable_games) >= 5:
                        break
        
        return suitable_games[:5]  # Limit to 5 games

    def _generate_questions_for_game(self, game_id: str, age_group: str) -> List[Dict]:
        """Generate questions for a specific game"""
        
        questions = []
        
        if game_id == 'math_magic':
            questions = self._generate_math_questions(age_group)
        elif game_id == 'word_wizard':
            questions = self._generate_language_questions(age_group)
        elif game_id == 'science_explorer':
            questions = self._generate_science_questions(age_group)
        elif game_id == 'history_hunter':
            questions = self._generate_history_questions(age_group)
        elif game_id == 'creative_crafter':
            questions = self._generate_creative_questions(age_group)
        
        return questions

    def _generate_math_questions(self, age_group: str) -> List[Dict]:
        """Generate age-appropriate math questions"""
        
        questions = []
        
        if age_group == '3-6':
            # Simple counting and basic arithmetic
            questions = [
                {
                    'id': 'math_1',
                    'question': '🐻 Count the bears! How many bears are there?',
                    'type': 'counting',
                    'visual': '🐻🐻🐻',
                    'options': ['1', '2', '3', '4'],
                    'correct': '3',
                    'explanation': 'Great counting! There are 3 cute bears!',
                    'points': 10
                },
                {
                    'id': 'math_2',
                    'question': '🍎 If you have 2 apples and get 1 more, how many do you have?',
                    'type': 'addition',
                    'visual': '🍎🍎 + 🍎 = ?',
                    'options': ['2', '3', '4', '5'],
                    'correct': '3',
                    'explanation': 'Perfect! 2 + 1 = 3 apples!',
                    'points': 15
                }
            ]
        elif age_group == '6-12':
            # Arithmetic and basic problem solving
            questions = [
                {
                    'id': 'math_3',
                    'question': '🏰 A magical castle has 24 windows. If 8 windows are on the first floor and 10 on the second floor, how many are on the third floor?',
                    'type': 'word_problem',
                    'visual': '🏰',
                    'options': ['4', '5', '6', '7'],
                    'correct': '6',
                    'explanation': 'Excellent! 24 - 8 - 10 = 6 windows on the third floor!',
                    'points': 20
                },
                {
                    'id': 'math_4',
                    'question': '🎪 At the circus tent, there are 5 rows of seats with 8 seats in each row. How many seats are there in total?',
                    'type': 'multiplication',
                    'visual': '🎪',
                    'options': ['35', '40', '45', '50'],
                    'correct': '40',
                    'explanation': 'Amazing! 5 × 8 = 40 seats for the circus!',
                    'points': 25
                }
            ]
        else:  # 12-18
            # Advanced math concepts
            questions = [
                {
                    'id': 'math_5',
                    'question': '🚀 A rocket travels at 500 km/h. How far will it travel in 2.5 hours?',
                    'type': 'algebra',
                    'visual': '🚀',
                    'options': ['1000 km', '1200 km', '1250 km', '1500 km'],
                    'correct': '1250 km',
                    'explanation': 'Perfect! Distance = Speed × Time = 500 × 2.5 = 1250 km!',
                    'points': 30
                }
            ]
        
        return questions

    def _generate_language_questions(self, age_group: str) -> List[Dict]:
        """Generate age-appropriate language questions"""
        
        questions = []
        
        if age_group == '6-12':
            questions = [
                {
                    'id': 'lang_1',
                    'question': '🦋 Which word rhymes with "butterfly"?',
                    'type': 'rhyming',
                    'visual': '🦋',
                    'options': ['cat', 'fly', 'tree', 'book'],
                    'correct': 'fly',
                    'explanation': 'Great job! "Butterfly" and "fly" rhyme!',
                    'points': 15
                },
                {
                    'id': 'lang_2',
                    'question': '📚 Complete the sentence: "The brave knight _____ the dragon."',
                    'type': 'grammar',
                    'visual': '🐉⚔️',
                    'options': ['fight', 'fights', 'fought', 'fighting'],
                    'correct': 'fought',
                    'explanation': 'Excellent! "Fought" is the past tense of fight!',
                    'points': 20
                }
            ]
        else:  # 12-18
            questions = [
                {
                    'id': 'lang_3',
                    'question': '🌟 What does the word "luminous" mean?',
                    'type': 'vocabulary',
                    'visual': '🌟',
                    'options': ['Very loud', 'Giving off light', 'Very small', 'Moving fast'],
                    'correct': 'Giving off light',
                    'explanation': 'Perfect! Luminous means giving off or reflecting light!',
                    'points': 25
                }
            ]
        
        return questions

    def _generate_science_questions(self, age_group: str) -> List[Dict]:
        """Generate age-appropriate science questions"""
        
        questions = []
        
        if age_group == '6-12':
            questions = [
                {
                    'id': 'sci_1',
                    'question': '🌱 What do plants need to grow?',
                    'type': 'biology',
                    'visual': '🌱☀️💧',
                    'options': ['Only water', 'Only sunlight', 'Water, sunlight, and air', 'Only soil'],
                    'correct': 'Water, sunlight, and air',
                    'explanation': 'Wonderful! Plants need water, sunlight, and air to grow healthy!',
                    'points': 20
                },
                {
                    'id': 'sci_2',
                    'question': '🌈 How many colors are in a rainbow?',
                    'type': 'physics',
                    'visual': '🌈',
                    'options': ['5', '6', '7', '8'],
                    'correct': '7',
                    'explanation': 'Amazing! A rainbow has 7 colors: Red, Orange, Yellow, Green, Blue, Indigo, Violet!',
                    'points': 15
                }
            ]
        else:  # 12-18
            questions = [
                {
                    'id': 'sci_3',
                    'question': '⚛️ What is the chemical symbol for gold?',
                    'type': 'chemistry',
                    'visual': '⚛️',
                    'options': ['Go', 'Gd', 'Au', 'Ag'],
                    'correct': 'Au',
                    'explanation': 'Excellent! Au comes from the Latin word "aurum" meaning gold!',
                    'points': 30
                }
            ]
        
        return questions

    def _generate_history_questions(self, age_group: str) -> List[Dict]:
        """Generate age-appropriate history questions"""
        
        questions = []
        
        if age_group == '9-12':
            questions = [
                {
                    'id': 'hist_1',
                    'question': '🏰 In which country would you find the Great Wall?',
                    'type': 'geography',
                    'visual': '🏯',
                    'options': ['Japan', 'China', 'India', 'Korea'],
                    'correct': 'China',
                    'explanation': 'Perfect! The Great Wall of China is one of the world\'s greatest wonders!',
                    'points': 20
                }
            ]
        else:  # 12-18
            questions = [
                {
                    'id': 'hist_2',
                    'question': '🗽 In which year did World War II end?',
                    'type': 'history',
                    'visual': '🕊️',
                    'options': ['1944', '1945', '1946', '1947'],
                    'correct': '1945',
                    'explanation': 'Correct! World War II ended in 1945, bringing peace to the world!',
                    'points': 25
                }
            ]
        
        return questions

    def _generate_creative_questions(self, age_group: str) -> List[Dict]:
        """Generate creative assessment questions"""
        
        questions = []
        
        if age_group in ['3-6', '6-12']:
            questions = [
                {
                    'id': 'art_1',
                    'question': '🎨 If you could paint anything magical, what would it be?',
                    'type': 'creative_expression',
                    'visual': '🎨✨',
                    'options': ['Flying unicorn', 'Rainbow castle', 'Talking flowers', 'All of these!'],
                    'correct': 'All of these!',
                    'explanation': 'Wonderful imagination! All creative ideas are amazing!',
                    'points': 15
                },
                {
                    'id': 'music_1',
                    'question': '🎵 Which instrument makes the highest sound?',
                    'type': 'music',
                    'visual': '🎵🎶',
                    'options': ['Piano', 'Flute', 'Drum', 'Guitar'],
                    'correct': 'Flute',
                    'explanation': 'Great ear! The flute makes beautiful high-pitched sounds!',
                    'points': 20
                }
            ]
        
        return questions

    def process_answer(self, session_id: str, question_id: str, answer: str, user_id: int) -> Dict:
        """Process user's answer and provide adaptive feedback"""
        
        # Get current question details
        result = {
            'correct': False,
            'points_earned': 0,
            'feedback': '',
            'explanation': '',
            'difficulty_adjustment': 0,
            'learning_insights': []
        }
        
        # This would typically fetch from session storage
        # For now, we'll simulate the logic
        
        # AI-powered response analysis
        analysis = self.ai_service.analyze_learning_response({
            'question_id': question_id,
            'user_answer': answer,
            'user_id': user_id,
            'context': 'knowledge_assessment'
        })
        
        result.update(analysis)
        
        # Update user's learning profile
        self.analytics.update_learning_profile(user_id, {
            'question_type': analysis.get('question_type'),
            'performance': analysis.get('performance_score', 0),
            'learning_style_indicators': analysis.get('learning_style_indicators', [])
        })
        
        return result

    def generate_final_assessment(self, session_id: str, user_id: int) -> Dict:
        """Generate comprehensive assessment results"""
        
        # This would aggregate all session data
        assessment = {
            'user_id': user_id,
            'session_id': session_id,
            'completion_date': datetime.now().isoformat(),
            'overall_score': 0,
            'subject_scores': {},
            'learning_profile': {
                'strengths': [],
                'improvement_areas': [],
                'recommended_difficulty': 2,
                'learning_style': 'visual',  # visual, auditory, kinesthetic, mixed
                'interests': []
            },
            'personalized_recommendations': {
                'next_lessons': [],
                'games_to_try': [],
                'difficulty_adjustments': {}
            },
            'achievements_unlocked': [],
            'pet_rewards': {
                'exp_gained': 0,
                'new_accessories': [],
                'care_points': 0
            }
        }
        
        # AI-powered comprehensive analysis
        ai_assessment = self.ai_service.generate_learning_assessment(user_id, session_id)
        assessment.update(ai_assessment)
        
        # Store assessment results
        self.analytics.store_assessment_results(user_id, assessment)
        
        return assessment

    def get_encouraging_messages(self, performance: str) -> List[str]:
        """Get encouraging messages based on performance"""
        
        messages = {
            'excellent': [
                "🌟 You're absolutely amazing! Your brain is like a supercomputer!",
                "🚀 Wow! You're ready to explore the universe of knowledge!",
                "🏆 Outstanding work! You're a true learning champion!",
                "✨ Incredible! Your curiosity lights up the whole world!"
            ],
            'good': [
                "🌈 Great job! You're growing smarter every day!",
                "🌱 Wonderful progress! Keep blooming like a beautiful flower!",
                "⭐ You're doing fantastic! Every question makes you stronger!",
                "🎈 Amazing effort! You're floating higher and higher!"
            ],
            'needs_practice': [
                "🌸 Every expert was once a beginner! You're on the right path!",
                "🐛 Like a caterpillar becoming a butterfly, you're transforming!",
                "🌟 Practice makes progress! You're shining brighter each day!",
                "🌳 Strong trees grow slowly but surely, just like you!"
            ]
        }
        
        return random.choice(messages.get(performance, messages['good']))

    def generate_adaptive_hints(self, question_id: str, user_profile: Dict) -> List[str]:
        """Generate personalized hints based on user's learning profile"""
        
        learning_style = user_profile.get('learning_style', 'visual')
        difficulty = user_profile.get('current_difficulty', 2)
        
        # AI-generated adaptive hints
        hints = self.ai_service.generate_adaptive_hints({
            'question_id': question_id,
            'learning_style': learning_style,
            'difficulty_level': difficulty,
            'user_preferences': user_profile.get('preferences', {})
        })
        
        return hints

    def create_mini_game_variant(self, base_question: Dict, user_profile: Dict) -> Dict:
        """Create engaging mini-game variants of questions"""
        
        learning_style = user_profile.get('learning_style', 'visual')
        age_group = user_profile.get('age_group', '6-12')
        
        if learning_style == 'kinesthetic':
            # Add drag-and-drop or interactive elements
            base_question['interaction_type'] = 'drag_drop'
            base_question['game_elements'] = {
                'animation': 'bounce',
                'sound_effects': True,
                'haptic_feedback': True
            }
        elif learning_style == 'auditory':
            # Add audio elements
            base_question['audio_question'] = True
            base_question['background_music'] = 'gentle_chimes'
            base_question['voice_narration'] = True
        else:  # visual
            # Enhanced visual elements
            base_question['visual_enhancements'] = {
                'animations': ['sparkle', 'glow'],
                'color_scheme': 'rainbow',
                'illustrations': 'detailed'
            }
        
        return base_question