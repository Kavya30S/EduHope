"""
Enhanced Adaptive Learning Service with Real-time AI Training
Personalizes learning experiences based on user interactions and performance
"""
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.models.user import User
from app.models.lesson import Lesson
from app.models.game_progress import GameProgress
from app import db

logger = logging.getLogger(__name__)

class AdaptiveLearningService:
    """Real-time adaptive learning system with AI personalization"""
    
    def __init__(self):
        self.learning_styles = {
            'visual': {'weight': 0.25, 'activities': ['image_games', 'color_matching', 'pattern_recognition']},
            'auditory': {'weight': 0.25, 'activities': ['music_games', 'story_listening', 'sound_matching']},
            'kinesthetic': {'weight': 0.25, 'activities': ['drag_drop', 'gesture_games', 'movement_activities']},
            'reading': {'weight': 0.25, 'activities': ['text_games', 'word_puzzles', 'reading_comprehension']}
        }
        
        self.difficulty_levels = {
            'beginner': {'multiplier': 0.8, 'min_accuracy': 0.0, 'max_accuracy': 0.6},
            'intermediate': {'multiplier': 1.0, 'min_accuracy': 0.6, 'max_accuracy': 0.8},
            'advanced': {'multiplier': 1.2, 'min_accuracy': 0.8, 'max_accuracy': 1.0}
        }
        
        self.engagement_factors = {
            'time_spent': 0.3,
            'interaction_frequency': 0.2,
            'completion_rate': 0.25,
            'retry_attempts': 0.15,
            'pet_interaction': 0.1
        }
    
    def analyze_learning_pattern(self, user_id: int, days_back: int = 7) -> Dict:
        """Analyze user's learning patterns with real-time updates"""
        try:
            user = User.query.get(user_id)
            if not user:
                return self._default_learning_profile()
            
            # Get recent learning data
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            recent_progress = GameProgress.query.filter(
                GameProgress.user_id == user_id,
                GameProgress.created_at >= cutoff_date
            ).all()
            
            if not recent_progress:
                return self._default_learning_profile()
            
            # Analyze performance patterns
            performance_data = self._analyze_performance(recent_progress)
            learning_style = self._detect_learning_style(recent_progress)
            engagement_level = self._calculate_engagement(recent_progress)
            difficulty_preference = self._assess_difficulty_preference(recent_progress)
            
            # Real-time adaptation
            adaptations = self._generate_adaptations(
                performance_data, learning_style, engagement_level, difficulty_preference
            )
            
            # Update user profile
            self._update_user_profile(user, {
                'learning_style': learning_style,
                'performance_metrics': performance_data,
                'engagement_level': engagement_level,
                'difficulty_preference': difficulty_preference,
                'adaptations': adaptations
            })
            
            return {
                'user_id': user_id,
                'learning_style': learning_style,
                'performance_metrics': performance_data,
                'engagement_level': engagement_level,
                'difficulty_preference': difficulty_preference,
                'recommended_activities': adaptations['activities'],
                'suggested_schedule': adaptations['schedule'],
                'motivation_triggers': adaptations['motivation'],
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing learning pattern for user {user_id}: {str(e)}")
            return self._default_learning_profile()
    
    def _analyze_performance(self, progress_data: List[GameProgress]) -> Dict:
        """Analyze performance metrics from game progress"""
        if not progress_data:
            return {'accuracy': 0.5, 'speed': 1.0, 'consistency': 0.5, 'improvement_rate': 0.0}
        
        accuracies = [p.score / 100.0 for p in progress_data if p.score is not None]
        times = [p.time_spent for p in progress_data if p.time_spent is not None]
        
        accuracy = np.mean(accuracies) if accuracies else 0.5
        avg_time = np.mean(times) if times else 60.0
        speed = max(0.1, min(2.0, 60.0 / avg_time))  # Normalize to 0.1-2.0 range
        
        # Calculate consistency (inverse of standard deviation)
        consistency = 1.0 - (np.std(accuracies) if len(accuracies) > 1 else 0.5)
        
        # Calculate improvement rate
        if len(accuracies) >= 3:
            recent_avg = np.mean(accuracies[-3:])
            older_avg = np.mean(accuracies[:-3])
            improvement_rate = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0.0
        else:
            improvement_rate = 0.0
        
        return {
            'accuracy': round(accuracy, 3),
            'speed': round(speed, 3),
            'consistency': round(consistency, 3),
            'improvement_rate': round(improvement_rate, 3),
            'total_sessions': len(progress_data)
        }
    
    def _detect_learning_style(self, progress_data: List[GameProgress]) -> Dict:
        """Detect preferred learning style based on activity performance"""
        style_scores = defaultdict(float)
        
        for progress in progress_data:
            game_type = progress.game_type
            score = progress.score / 100.0 if progress.score else 0.5
            
            # Map game types to learning styles
            if game_type in ['color_match', 'pattern_game', 'visual_memory']:
                style_scores['visual'] += score
            elif game_type in ['sound_match', 'music_rhythm', 'story_listening']:
                style_scores['auditory'] += score
            elif game_type in ['drag_drop', 'gesture_game', 'movement_puzzle']:
                style_scores['kinesthetic'] += score
            elif game_type in ['word_puzzle', 'reading_game', 'text_adventure']:
                style_scores['reading'] += score
        
        # Normalize scores
        total_score = sum(style_scores.values())
        if total_score > 0:
            for style in style_scores:
                style_scores[style] /= total_score
        else:
            # Default balanced distribution
            style_scores = {style: 0.25 for style in self.learning_styles.keys()}
        
        return dict(style_scores)
    
    def _calculate_engagement(self, progress_data: List[GameProgress]) -> Dict:
        """Calculate engagement metrics"""
        if not progress_data:
            return {'level': 0.5, 'patterns': {}, 'peak_times': []}
        
        total_time = sum(p.time_spent for p in progress_data if p.time_spent)
        avg_session_time = total_time / len(progress_data) if progress_data else 0
        
        completion_rates = [1.0 if p.completed else 0.0 for p in progress_data]
        avg_completion = np.mean(completion_rates)
        
        # Analyze time patterns
        hour_engagement = defaultdict(list)
        for progress in progress_data:
            hour = progress.created_at.hour
            engagement_score = (progress.score / 100.0) * (1.0 if progress.completed else 0.5)
            hour_engagement[hour].append(engagement_score)
        
        peak_hours = []
        for hour, scores in hour_engagement.items():
            if len(scores) >= 2 and np.mean(scores) > 0.7:
                peak_hours.append(hour)
        
        # Overall engagement level
        engagement_level = (avg_completion * 0.4 + 
                          min(avg_session_time / 300, 1.0) * 0.3 +  # Cap at 5 minutes
                          (len(progress_data) / 7) * 0.3)  # Weekly frequency
        
        return {
            'level': round(min(engagement_level, 1.0), 3),
            'avg_session_time': round(avg_session_time, 1),
            'completion_rate': round(avg_completion, 3),
            'peak_hours': sorted(peak_hours),
            'consistency': len(progress_data) / 7  # Sessions per day
        }
    
    def _assess_difficulty_preference(self, progress_data: List[GameProgress]) -> Dict:
        """Assess optimal difficulty level for user"""
        difficulty_performance = defaultdict(list)
        
        for progress in progress_data:
            difficulty = progress.difficulty or 'intermediate'
            score = progress.score / 100.0 if progress.score else 0.5
            difficulty_performance[difficulty].append(score)
        
        optimal_difficulty = 'intermediate'
        best_score = 0.0
        
        for difficulty, scores in difficulty_performance.items():
            if len(scores) >= 2:
                avg_score = np.mean(scores)
                if avg_score > best_score:
                    best_score = avg_score
                    optimal_difficulty = difficulty
        
        return {
            'current_optimal': optimal_difficulty,
            'performance_by_level': {
                level: round(np.mean(scores), 3) if scores else 0.0
                for level, scores in difficulty_performance.items()
            },
            'recommended_progression': self._suggest_difficulty_progression(difficulty_performance)
        }
    
    def _suggest_difficulty_progression(self, difficulty_data: Dict) -> List[str]:
        """Suggest difficulty progression path"""
        current_levels = list(difficulty_data.keys())
        
        if not current_levels:
            return ['beginner', 'intermediate', 'advanced']
        
        # Analyze performance to suggest next steps
        progression = []
        
        if 'beginner' in current_levels:
            beginner_avg = np.mean(difficulty_data['beginner'])
            if beginner_avg >= 0.8:
                progression.append('intermediate')
            else:
                progression.append('beginner')
        
        if 'intermediate' in current_levels:
            intermediate_avg = np.mean(difficulty_data['intermediate'])
            if intermediate_avg >= 0.8:
                progression.append('advanced')
            elif intermediate_avg >= 0.6:
                progression.append('intermediate')
            else:
                progression.append('beginner')
        
        if not progression:
            progression = ['intermediate']
        
        return progression
    
    def _generate_adaptations(self, performance: Dict, learning_style: Dict, 
                            engagement: Dict, difficulty: Dict) -> Dict:
        """Generate personalized adaptations"""
        
        # Recommend activities based on learning style
        preferred_style = max(learning_style.items(), key=lambda x: x[1])[0]
        recommended_activities = self.learning_styles[preferred_style]['activities'].copy()
        
        # Add variety from other styles
        for style, weight in learning_style.items():
            if style != preferred_style and weight > 0.15:
                recommended_activities.extend(self.learning_styles[style]['activities'][:2])
        
        # Generate schedule based on engagement patterns
        peak_times = engagement.get('peak_hours', [])
        if not peak_times:
            peak_times = [9, 15, 19]  # Default peak times
        
        schedule = {
            'optimal_times': peak_times,
            'session_duration': min(max(int(engagement.get('avg_session_time', 180)), 120), 600),
            'frequency': 'daily' if engagement['level'] > 0.7 else 'every_other_day',
            'break_intervals': 300 if engagement['level'] < 0.5 else 600
        }
        
        # Motivation triggers based on performance
        motivation_triggers = []
        if performance['accuracy'] < 0.6:
            motivation_triggers.extend(['encouragement', 'easier_tasks', 'pet_rewards'])
        if performance['consistency'] < 0.5:
            motivation_triggers.extend(['routine_building', 'progress_tracking'])
        if engagement['level'] < 0.5:
            motivation_triggers.extend(['variety', 'social_features', 'achievements'])
        
        return {
            'activities': recommended_activities,
            'schedule': schedule,
            'motivation': motivation_triggers,
            'difficulty_adjustment': difficulty['current_optimal']
        }
    
    def _update_user_profile(self, user: User, learning_data: Dict):
        """Update user's learning profile in database"""
        try:
            # Store learning profile as JSON
            user.learning_profile = json.dumps({
                'learning_style': learning_data['learning_style'],
                'performance_metrics': learning_data['performance_metrics'],
                'engagement_level': learning_data['engagement_level'],
                'difficulty_preference': learning_data['difficulty_preference'],
                'last_analysis': datetime.utcnow().isoformat()
            })
            
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            db.session.rollback()
    
    def _default_learning_profile(self) -> Dict:
        """Return default learning profile for new users"""
        return {
            'learning_style': {style: 0.25 for style in self.learning_styles.keys()},
            'performance_metrics': {
                'accuracy': 0.5,
                'speed': 1.0,
                'consistency': 0.5,
                'improvement_rate': 0.0,
                'total_sessions': 0
            },
            'engagement_level': {
                'level': 0.5,
                'avg_session_time': 180,
                'completion_rate': 0.5,
                'peak_hours': [9, 15, 19],
                'consistency': 0.5
            },
            'difficulty_preference': {
                'current_optimal': 'beginner',
                'performance_by_level': {},
                'recommended_progression': ['beginner', 'intermediate']
            },
            'recommended_activities': ['color_match', 'sound_match', 'word_puzzle'],
            'suggested_schedule': {
                'optimal_times': [9, 15, 19],
                'session_duration': 180,
                'frequency': 'daily',
                'break_intervals': 300
            },
            'motivation_triggers': ['encouragement', 'pet_rewards', 'achievements']
        }
    
    def get_personalized_content(self, user_id: int, content_type: str) -> List[Dict]:
        """Get personalized content recommendations"""
        learning_profile = self.analyze_learning_pattern(user_id)
        
        # Get content based on learning style and difficulty
        preferred_style = max(learning_profile['learning_style'].items(), key=lambda x: x[1])[0]
        difficulty = learning_profile['difficulty_preference']['current_optimal']
        
        # Query lessons based on preferences
        lessons = Lesson.query.filter(
            Lesson.difficulty == difficulty,
            Lesson.learning_style.contains(preferred_style)
        ).limit(10).all()
        
        if not lessons:
            # Fallback to any available lessons
            lessons = Lesson.query.filter(Lesson.difficulty == difficulty).limit(10).all()
        
        return [lesson.to_dict() for lesson in lessons]
    
    def update_real_time_progress(self, user_id: int, game_data: Dict) -> Dict:
        """Update learning model with real-time game data"""
        try:
            # Create progress record
            progress = GameProgress(
                user_id=user_id,
                game_type=game_data.get('game_type', 'unknown'),
                score=game_data.get('score', 0),
                time_spent=game_data.get('time_spent', 0),
                difficulty=game_data.get('difficulty', 'intermediate'),
                completed=game_data.get('completed', False),
                mistakes=game_data.get('mistakes', 0),
                hints_used=game_data.get('hints_used', 0)
            )
            
            db.session.add(progress)
            db.session.commit()
            
            # Immediate adaptation based on this session
            adaptations = self._immediate_adaptations(game_data)
            
            return {
                'success': True,
                'immediate_adaptations': adaptations,
                'next_recommendations': self._get_next_activity_recommendations(user_id, game_data)
            }
            
        except Exception as e:
            logger.error(f"Error updating real-time progress: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def _immediate_adaptations(self, game_data: Dict) -> Dict:
        """Generate immediate adaptations based on current session"""
        score = game_data.get('score', 0) / 100.0
        time_spent = game_data.get('time_spent', 180)
        mistakes = game_data.get('mistakes', 0)
        
        adaptations = {}
        
        # Difficulty adjustment
        if score >= 0.9 and mistakes <= 1:
            adaptations['difficulty'] = 'increase'
        elif score < 0.5 or mistakes > 5:
            adaptations['difficulty'] = 'decrease'
        else:
            adaptations['difficulty'] = 'maintain'
        
        # Pacing adjustment
        if time_spent < 60:
            adaptations['pacing'] = 'add_complexity'
        elif time_spent > 300:
            adaptations['pacing'] = 'simplify'
        else:
            adaptations['pacing'] = 'maintain'
        
        # Engagement boost
        if score < 0.6:
            adaptations['motivation'] = ['encouragement', 'pet_interaction', 'easier_variant']
        else:
            adaptations['motivation'] = ['celebration', 'challenge_unlock', 'progress_reward']
        
        return adaptations
    
    def _get_next_activity_recommendations(self, user_id: int, current_game: Dict) -> List[Dict]:
        """Get smart recommendations for next activities"""
        learning_profile = self.analyze_learning_pattern(user_id, days_back=1)
        
        current_type = current_game.get('game_type', '')
        current_performance = current_game.get('score', 0) / 100.0
        
        recommendations = []
        
        # If performed well, suggest similar or harder content
        if current_performance >= 0.8:
            recommendations.extend([
                {'type': 'similar_advanced', 'reason': 'You mastered this! Try a harder version.'},
                {'type': 'related_skill', 'reason': 'Ready for a new challenge?'}
            ])
        
        # If struggled, suggest supportive content
        elif current_performance < 0.5:
            recommendations.extend([
                {'type': 'easier_version', 'reason': 'Let\'s practice this more!'},
                {'type': 'different_approach', 'reason': 'Try a different way to learn this.'}
            ])
        
        # Always include variety based on learning style
        preferred_style = max(learning_profile['learning_style'].items(), key=lambda x: x[1])[0]
        recommendations.append({
            'type': f'{preferred_style}_activity',
            'reason': f'Perfect for your {preferred_style} learning style!'
        })
        
        return recommendations[:3]  # Return top 3 recommendations
    
    def get_learning_insights(self, user_id: int) -> Dict:
        """Get comprehensive learning insights for teachers/parents"""
        learning_profile = self.analyze_learning_pattern(user_id, days_back=30)
        
        # Get recent progress
        recent_progress = GameProgress.query.filter(
            GameProgress.user_id == user_id,
            GameProgress.created_at >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        # Calculate trends
        trends = self._calculate_learning_trends(recent_progress)
        
        return {
            'learning_profile': learning_profile,
            'trends': trends,
            'strengths': self._identify_strengths(learning_profile),
            'growth_areas': self._identify_growth_areas(learning_profile),
            'recommendations': self._generate_teacher_recommendations(learning_profile)
        }
    
    def _calculate_learning_trends(self, progress_data: List[GameProgress]) -> Dict:
        """Calculate learning trends over time"""
        if len(progress_data) < 3:
            return {'trend': 'insufficient_data'}
        
        # Sort by date
        progress_data.sort(key=lambda x: x.created_at)
        
        scores = [p.score for p in progress_data if p.score is not None]
        if len(scores) < 3:
            return {'trend': 'insufficient_data'}
        
        # Calculate trend using linear regression
        x = np.arange(len(scores))
        y = np.array(scores)
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 2:
            trend = 'improving_fast'
        elif slope > 0.5:
            trend = 'improving'
        elif slope > -0.5:
            trend = 'stable'
        elif slope > -2:
            trend = 'declining'
        else:
            trend = 'declining_fast'
        
        return {
            'trend': trend,
            'slope': round(slope, 2),
            'recent_average': round(np.mean(scores[-3:]), 1),
            'overall_average': round(np.mean(scores), 1)
        }
    
    def _identify_strengths(self, learning_profile: Dict) -> List[str]:
        """Identify user's learning strengths"""
        strengths = []
        
        performance = learning_profile['performance_metrics']
        if performance['accuracy'] >= 0.8:
            strengths.append('High accuracy in problem-solving')
        if performance['speed'] >= 1.5:
            strengths.append('Quick learner')
        if performance['consistency'] >= 0.8:
            strengths.append('Consistent performance')
        if performance['improvement_rate'] >= 0.1:
            strengths.append('Rapidly improving')
        
        engagement = learning_profile['engagement_level']
        if engagement['level'] >= 0.8:
            strengths.append('Highly engaged learner')
        if engagement['completion_rate'] >= 0.9:
            strengths.append('Excellent task completion')
        
        return strengths
    
    def _identify_growth_areas(self, learning_profile: Dict) -> List[str]:
        """Identify areas for improvement"""
        growth_areas = []
        
        performance = learning_profile['performance_metrics']
        if performance['accuracy'] < 0.6:
            growth_areas.append('Problem-solving accuracy')
        if performance['consistency'] < 0.5:
            growth_areas.append('Performance consistency')
        if performance['improvement_rate'] < 0:
            growth_areas.append('Learning progress')
        
        engagement = learning_profile['engagement_level']
        if engagement['level'] < 0.5:
            growth_areas.append('Learning engagement')
        if engagement['completion_rate'] < 0.7:
            growth_areas.append('Task completion')
        
        return growth_areas
    
    def _generate_teacher_recommendations(self, learning_profile: Dict) -> List[Dict]:
        """Generate recommendations for teachers/parents"""
        recommendations = []
        
        preferred_style = max(learning_profile['learning_style'].items(), key=lambda x: x[1])[0]
        
        recommendations.append({
            'category': 'Learning Style',
            'recommendation': f'Focus on {preferred_style} learning activities',
            'action': f'Use more {", ".join(self.learning_styles[preferred_style]["activities"])}'
        })
        
        engagement = learning_profile['engagement_level']
        if engagement['level'] < 0.6:
            recommendations.append({
                'category': 'Engagement',
                'recommendation': 'Increase engagement through variety and rewards',
                'action': 'Try shorter sessions with immediate feedback and pet interactions'
            })
        
        optimal_times = engagement.get('peak_hours', [])
        if optimal_times:
            recommendations.append({
                'category': 'Timing',
                'recommendation': f'Schedule learning during optimal hours: {optimal_times}',
                'action': 'Plan main learning activities during these peak performance times'
            })
        
        return recommendations