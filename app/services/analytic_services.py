import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    """
    Advanced learning analytics service that tracks, analyzes, and provides insights
    on user learning patterns, progress, and educational outcomes.
    """
    
    def __init__(self):
        self.user_analytics = {}
        self.global_analytics = {
            'total_users': 0,
            'total_sessions': 0,
            'total_learning_time': 0,
            'popular_subjects': defaultdict(int),
            'engagement_metrics': []
        }
        
    def track_learning_event(self, user_id: int, event_type: str, event_data: Dict) -> None:
        """Track individual learning events for analytics"""
        try:
            if user_id not in self.user_analytics:
                self.user_analytics[user_id] = {
                    'sessions': [],
                    'learning_events': [],
                    'achievements': [],
                    'skill_progress': defaultdict(list),
                    'engagement_timeline': [],
                    'emotional_journey': []
                }
            
            event = {
                'timestamp': datetime.now(),
                'type': event_type,
                'data': event_data,
                'session_id': event_data.get('session_id'),
                'subject': event_data.get('subject'),
                'difficulty': event_data.get('difficulty', 0.5)
            }
            
            self.user_analytics[user_id]['learning_events'].append(event)
            self._update_skill_progress(user_id, event)
            self._update_engagement_metrics(user_id, event)
            
        except Exception as e:
            logger.error(f"Error tracking learning event: {e}")
    
    def generate_progress_report(self, user_id: int, period_days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive progress report for a user"""
        try:
            if user_id not in self.user_analytics:
                return {'error': 'No analytics data available for this user'}
            
            analytics = self.user_analytics[user_id]
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # Filter events within the period
            period_events = [
                event for event in analytics['learning_events']
                if start_date <= event['timestamp'] <= end_date
            ]
            
            report = {
                'period': f"{period_days} days",
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'summary': self._generate_summary_stats(period_events),
                'skill_progression': self._analyze_skill_progression(user_id, period_events),
                'engagement_analysis': self._analyze_engagement_patterns(period_events),
                'learning_velocity': self._calculate_learning_velocity(period_events),
                'subject_mastery': self._assess_subject_mastery(period_events),
                'achievement_progress': self._track_achievement_progress(user_id, period_events),
                'recommendations': self._generate_improvement_recommendations(period_events),
                'celebration_moments': self._identify_celebration_moments(period_events),
                'challenge_areas': self._identify_challenge_areas(period_events)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating progress report: {e}")
            return {'error': 'Failed to generate progress report'}
    
    def analyze_learning_patterns(self, user_id: int) -> Dict[str, Any]:
        """Analyze detailed learning patterns and behaviors"""
        try:
            if user_id not in self.user_analytics:
                return {}
            
            analytics = self.user_analytics[user_id]
            events = analytics['learning_events']
            
            patterns = {
                'optimal_learning_times': self._find_optimal_learning_times(events),
                'session_length_preferences': self._analyze_session_lengths(events),
                'subject_preferences': self._analyze_subject_preferences(events),
                'difficulty_comfort_zone': self._find_difficulty_comfort_zone(events),
                'learning_style_indicators': self._detect_learning_style_patterns(events),
                'motivation_patterns': self._analyze_motivation_patterns(events),
                'attention_span_trends': self._track_attention_span_trends(events),
                'error_recovery_patterns': self._analyze_error_recovery(events)
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing learning patterns: {e}")
            return {}
    
    def get_real_time_insights(self, user_id: int, current_session: Dict) -> Dict[str, Any]:
        """Provide real-time insights during active learning session"""
        try:
            insights = {
                'current_performance': self._assess_current_performance(current_session),
                'engagement_level': self._measure_current_engagement(current_session),
                'optimal_break_suggestion': self._suggest_break_timing(user_id, current_session),
                'difficulty_adjustment': self._recommend_difficulty_adjustment(user_id, current_session),
                'encouragement_trigger': self._check_encouragement_triggers(current_session),
                'achievement_proximity': self._check_achievement_proximity(user_id, current_session),
                'learning_momentum': self._assess_learning_momentum(current_session)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting real-time insights: {e}")
            return {}
    
    def compare_peer_performance(self, user_id: int, age_group: str = None) -> Dict[str, Any]:
        """Compare user performance with anonymized peer data"""
        try:
            user_metrics = self._get_user_metrics(user_id)
            peer_metrics = self._get_peer_metrics(age_group)
            
            if not user_metrics or not peer_metrics:
                return {'error': 'Insufficient data for comparison'}
            
            comparison = {
                'percentile_ranking': self._calculate_percentile_ranking(user_metrics, peer_metrics),
                'strength_areas': self._identify_relative_strengths(user_metrics, peer_metrics),
                'growth_opportunities': self._identify_growth_opportunities(user_metrics, peer_metrics),
                'learning_pace_comparison': self._compare_learning_pace(user_metrics, peer_metrics),
                'engagement_comparison': self._compare_engagement_levels(user_metrics, peer_metrics),
                'achievement_comparison': self._compare_achievements(user_id, peer_metrics)
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing peer performance: {e}")
            return {}
    
    def predict_learning_outcomes(self, user_id: int, time_horizon: int = 30) -> Dict[str, Any]:
        """Predict learning outcomes based on current patterns"""
        try:
            if user_id not in self.user_analytics:
                return {}
            
            analytics = self.user_analytics[user_id]
            historical_data = self._prepare_historical_data(analytics)
            
            predictions = {
                'skill_progression_forecast': self._predict_skill_progression(historical_data, time_horizon),
                'engagement_forecast': self._predict_engagement_trends(historical_data, time_horizon),
                'achievement_timeline': self._predict_achievement_timeline(user_id, time_horizon),
                'learning_goals_feasibility': self._assess_goal_feasibility(user_id, time_horizon),
                'potential_challenges': self._predict_potential_challenges(historical_data),
                'success_probability': self._calculate_success_probability(historical_data),
                'recommended_interventions': self._recommend_interventions(historical_data)
            }
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting learning outcomes: {e}")
            return {}
    
    def _generate_summary_stats(self, events: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics from events"""
        if not events:
            return {}
        
        total_time = sum(event['data'].get('duration', 0) for event in events)
        total_questions = sum(event['data'].get('questions_answered', 0) for event in events)
        correct_answers = sum(event['data'].get('correct_answers', 0) for event in events)
        
        return {
            'total_sessions': len(set(event.get('session_id') for event in events if event.get('session_id'))),
            'total_learning_time_minutes': total_time,
            'total_questions_answered': total_questions,
            'overall_accuracy': correct_answers / total_questions if total_questions > 0 else 0,
            'average_session_length': total_time / len(events) if events else 0,
            'subjects_explored': len(set(event.get('subject') for event in events if event.get('subject'))),
            'learning_streak_days': self._calculate_learning_streak_from_events(events)
        }
    
    def _analyze_skill_progression(self, user_id: int, events: List[Dict]) -> Dict[str, Any]:
        """Analyze skill progression over time"""
        skill_data = defaultdict(list)
        
        for event in events:
            subject = event.get('subject')
            accuracy = event['data'].get('accuracy', 0)
            timestamp = event['timestamp']
            
            if subject and accuracy:
                skill_data[subject].append({
                    'timestamp': timestamp,
                    'accuracy': accuracy,
                    'difficulty': event.get('difficulty', 0.5)
                })
        
        progression = {}
        for subject, data in skill_data.items():
            if len(data) >= 2:
                sorted_data = sorted(data, key=lambda x: x['timestamp'])
                initial_accuracy = sorted_data[0]['accuracy']
                current_accuracy = sorted_data[-1]['accuracy']
                improvement = current_accuracy - initial_accuracy
                
                progression[subject] = {
                    'improvement': improvement,
                    'current_level': current_accuracy,
                    'trend': 'improving' if improvement > 0.1 else 'stable' if abs(improvement) <= 0.1 else 'needs_attention',
                    'sessions_count': len(data),
                    'difficulty_progression': self._analyze_difficulty_progression(sorted_data)
                }
        
        return progression
    
    def _analyze_engagement_patterns(self, events: List[Dict]) -> Dict[str, Any]:
        """Analyze engagement patterns from events"""
        engagement_scores = [event['data'].get('engagement_score', 0.5) for event in events]
        session_lengths = [event['data'].get('duration', 0) for event in events]
        
        if not engagement_scores:
            return {}
        
        return {
            'average_engagement': np.mean(engagement_scores),
            'engagement_trend': self._calculate_trend(engagement_scores),
            'peak_engagement_times': self._find_peak_engagement_times(events),
            'engagement_consistency': np.std(engagement_scores),
            'optimal_session_length': self._find_optimal_session_length(session_lengths, engagement_scores)
        }
    
    def _calculate_learning_velocity(self, events: List[Dict]) -> Dict[str, Any]:
        """Calculate how quickly user is learning new concepts"""
        if len(events) < 2:
            return {}
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda x: x['timestamp'])
        
        # Calculate velocity metrics
        time_span = (sorted_events[-1]['timestamp'] - sorted_events[0]['timestamp']).days
        concepts_learned = len(set(event['data'].get('concept') for event in events if event['data'].get('concept')))
        accuracy_improvement = self._calculate_overall_accuracy_improvement(sorted_events)
        
        return {
            'concepts_per_day': concepts_learned / max(time_span, 1),
            'accuracy_improvement_rate': accuracy_improvement / max(time_span, 1),
            'learning_acceleration': self._calculate_learning_acceleration(sorted_events),
            'mastery_speed': self._calculate_mastery_speed(sorted_events)
        }
    
    def _assess_subject_mastery(self, events: List[Dict]) -> Dict[str, Any]:
        """Assess mastery level for different subjects"""
        subject_data = defaultdict(list)
        
        for event in events:
            subject = event.get('subject')
            if subject:
                subject_data[subject].append({
                    'accuracy': event['data'].get('accuracy', 0),
                    'difficulty': event.get('difficulty', 0.5),
                    'timestamp': event['timestamp']
                })
        
        mastery_levels = {}
        for subject, data in subject_data.items():
            if data:
                avg_accuracy = np.mean([d['accuracy'] for d in data])
                avg_difficulty = np.mean([d['difficulty'] for d in data])
                consistency = 1 - np.std([d['accuracy'] for d in data])
                
                # Calculate mastery score (0-1)
                mastery_score = (avg_accuracy * 0.5 + avg_difficulty * 0.3 + consistency * 0.2)
                
                mastery_levels[subject] = {
                    'mastery_score': mastery_score,
                    'level': self._determine_mastery_level(mastery_score),
                    'sessions_count': len(data),
                    'recommendation': self._get_mastery_recommendation(mastery_score, subject)
                }
        
        return mastery_levels
    
    def _track_achievement_progress(self, user_id: int, events: List[Dict]) -> Dict[str, Any]:
        """Track progress toward achievements"""
        # This would integrate with the achievement system
        achievements_progress = {
            'completed_achievements': [],
            'in_progress_achievements': [],
            'available_achievements': [],
            'achievement_points': 0
        }
        
        # Calculate achievement metrics from events
        total_questions = sum(event['data'].get('questions_answered', 0) for event in events)
        total_correct = sum(event['data'].get('correct_answers', 0) for event in events)
        subjects_explored = len(set(event.get('subject') for event in events if event.get('subject')))
        
        # Example achievement tracking
        if total_questions >= 100:
            achievements_progress['completed_achievements'].append('Question Master')
        
        if total_correct >= 50:
            achievements_progress['completed_achievements'].append('Accuracy Expert')
        
        if subjects_explored >= 3:
            achievements_progress['completed_achievements'].append('Explorer')
        
        return achievements_progress
    
    def _generate_improvement_recommendations(self, events: List[Dict]) -> List[str]:
        """Generate personalized improvement recommendations"""
        recommendations = []
        
        if not events:
            return ['Start your learning journey with basic lessons!']
        
        # Analyze patterns and generate recommendations
        accuracy_scores = [event['data'].get('accuracy', 0) for event in events]
        avg_accuracy = np.mean(accuracy_scores) if accuracy_scores else 0
        
        engagement_scores = [event['data'].get('engagement_score', 0.5) for event in events]
        avg_engagement = np.mean(engagement_scores) if engagement_scores else 0.5
        
        if avg_accuracy < 0.6:
            recommendations.append("Focus on understanding fundamentals before moving to advanced topics")
        
        if avg_engagement < 0.5:
            recommendations.append("Try shorter learning sessions with more interactive activities")
        
        # Subject-specific recommendations
        subjects_performance = defaultdict(list)
        for event in events:
            subject = event.get('subject')
            if subject:
                subjects_performance[subject].append(event['data'].get('accuracy', 0))
        
        for subject, accuracies in subjects_performance.items():
            avg_subject_accuracy = np.mean(accuracies)
            if avg_subject_accuracy < 0.7:
                recommendations.append(f"Spend more time practicing {subject} fundamentals")
        
        return recommendations or ['Keep up the great work!']
    
    def _identify_celebration_moments(self, events: List[Dict]) -> List[Dict]:
        """Identify moments worthy of celebration"""
        celebrations = []
        
        # Look for improvement streaks
        accuracy_scores = [(event['timestamp'], event['data'].get('accuracy', 0)) for event in events]
        accuracy_scores.sort(key=lambda x: x[0])
        
        streak_count = 0
        for i in range(1, len(accuracy_scores)):
            if accuracy_scores[i][1] >= accuracy_scores[i-1][1]:
                streak_count += 1
            else:
                if streak_count >= 3:
                    celebrations.append({
                        'type': 'improvement_streak',
                        'description': f'Amazing! {streak_count} sessions of continuous improvement!',
                        'date': accuracy_scores[i-1][0].strftime('%Y-%m-%d')
                    })
                streak_count = 0
        
        # Look for perfect scores
        perfect_sessions = [event for event in events if event['data'].get('accuracy', 0) >= 0.95]
        if perfect_sessions:
            celebrations.append({
                'type': 'perfect_scores',
                'description': f'Incredible! {len(perfect_sessions)} perfect or near-perfect sessions!',
                'count': len(perfect_sessions)
            })
        
        return celebrations
    
    def _identify_challenge_areas(self, events: List[Dict]) -> List[Dict]:
        """Identify areas that need more attention"""
        challenge_areas = []
        
        # Subject-based challenges
        subject_performance = defaultdict(list)
        for event in events:
            subject = event.get('subject')
            if subject:
                subject_performance[subject].append(event['data'].get('accuracy', 0))
        
        for subject, accuracies in subject_performance.items():
            if accuracies and np.mean(accuracies) < 0.6:
                challenge_areas.append({
                    'type': 'subject_difficulty',
                    'subject': subject,
                    'average_accuracy': np.mean(accuracies),
                    'recommendation': f'Consider reviewing {subject} basics or requesting help'
                })
        
        # Engagement challenges
        engagement_scores = [event['data'].get('engagement_score', 0.5) for event in events]
        if engagement_scores and np.mean(engagement_scores) < 0.4:
            challenge_areas.append({
                'type': 'engagement_concern',
                'description': 'Learning engagement seems low',
                'recommendation': 'Try different learning activities or shorter sessions'
            })
        
        return challenge_areas
    
    def _find_optimal_learning_times(self, events: List[Dict]) -> Dict[str, Any]:
        """Find optimal learning times based on performance"""
        hourly_performance = defaultdict(list)
        
        for event in events:
            hour = event['timestamp'].hour
            accuracy = event['data'].get('accuracy', 0)
            engagement = event['data'].get('engagement_score', 0.5)
            
            hourly_performance[hour].append({
                'accuracy': accuracy,
                'engagement': engagement
            })
        
        optimal_hours = []
        for hour, performances in hourly_performance.items():
            if len(performances) >= 2:  # Need multiple sessions to be significant
                avg_accuracy = np.mean([p['accuracy'] for p in performances])
                avg_engagement = np.mean([p['engagement'] for p in performances])
                
                if avg_accuracy > 0.7 and avg_engagement > 0.6:
                    optimal_hours.append({
                        'hour': hour,
                        'performance_score': avg_accuracy * 0.6 + avg_engagement * 0.4,
                        'sessions_count': len(performances)
                    })
        
        optimal_hours.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return {
            'best_hours': optimal_hours[:3],
            'recommendation': self._generate_time_recommendation(optimal_hours)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values"""
        if len(values) < 2:
            return 'insufficient_data'
        
        # Simple linear trend calculation
        x = list(range(len(values)))
        y = values
        
        # Calculate slope
        n = len(values)
        slope = (n * sum(x[i] * y[i] for i in range(n)) - sum(x) * sum(y)) / (n * sum(x[i]**2 for i in range(n)) - sum(x)**2)
        
        if slope > 0.05:
            return 'improving'
        elif slope < -0.05:
            return 'declining'
        else:
            return 'stable'
    
    def _determine_mastery_level(self, mastery_score: float) -> str:
        """Determine mastery level from score"""
        if mastery_score >= 0.8:
            return 'expert'
        elif mastery_score >= 0.6:
            return 'proficient'
        elif mastery_score >= 0.4:
            return 'developing'
        else:
            return 'beginner'
    
    def get_dashboard_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get key metrics for user dashboard"""
        try:
            if user_id not in self.user_analytics:
                return self._get_default_dashboard_metrics()
            
            analytics = self.user_analytics[user_id]
            recent_events = [
                event for event in analytics['learning_events']
                if event['timestamp'] >= datetime.now() - timedelta(days=7)
            ]
            
            metrics = {
                'weekly_progress': self._calculate_weekly_progress(recent_events),
                'current_streak': self._calculate_current_streak(analytics['learning_events']),
                'favorite_subject': self._identify_favorite_subject(recent_events),
                'achievement_count': len(analytics.get('achievements', [])),
                'total_learning_time': self._calculate_total_learning_time(analytics['learning_events']),
                'accuracy_trend': self._get_accuracy_trend(recent_events),
                'next_milestone': self._get_next_milestone(user_id),
                'encouragement_message': self._generate_encouragement_message(recent_events)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            return self._get_default_dashboard_metrics()
    
    def _get_default_dashboard_metrics(self) -> Dict[str, Any]:
        """Get default dashboard metrics for new users"""
        return {
            'weekly_progress': 0,
            'current_streak': 0,
            'favorite_subject': 'Not determined yet',
            'achievement_count': 0,
            'total_learning_time': 0,
            'accuracy_trend': 'stable',
            'next_milestone': 'Complete your first lesson!',
            'encouragement_message': 'Welcome to your learning adventure! 🌟'
        }