from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
from app.models.lesson import Lesson
from app.models.user import User,LearningSession, UserMixin,UserProgress
from app.models.achievement import Achievement,UserAchievement
from app.models.pet import Pet
from app.models.emotion import EmotionalState
from app.services.llm_service import LLMService
from app.services.sentiment_service import SentimentService
from app.services.adaptive_learning_services import AdaptiveLearningService
from app import db
import re  # ADD THIS
from collections import Counter 
from typing import List, Dict, Any 
import random
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)



education_bp = Blueprint('education', __name__)
llm_service = LLMService()
sentiment_service = SentimentService()

def check_level_up(user):
    """Check if user should level up based on experience points"""
    # Level progression: 100 XP for level 1, +50 XP for each subsequent level
    required_xp = 100 + (user.level - 1) * 50
    return user.experience_points >= required_xp

def unlock_new_content(user):
    """Unlock new content based on user's level"""
    new_unlocks = []
    
    # Level-based unlocks
    unlocks_by_level = {
        2: ['advanced_math', 'story_mode'],
        3: ['science_basics', 'creative_writing'],
        4: ['history_adventures', 'coding_basics'],
        5: ['advanced_science', 'group_challenges'],
        10: ['mentor_mode', 'content_creation']
    }
    
    if user.level in unlocks_by_level:
        for unlock in unlocks_by_level[user.level]:
            # Add to user's unlocked content
            if not hasattr(user, 'unlocked_content'):
                user.unlocked_content = json.dumps([])
            
            unlocked = json.loads(user.unlocked_content)
            if unlock not in unlocked:
                unlocked.append(unlock)
                user.unlocked_content = json.dumps(unlocked)
                new_unlocks.append(unlock)
    
    return new_unlocks

def check_and_award_achievements(user, lesson, score):
    """Check and award achievements based on user actions"""
    achievements_to_award = []
    
    # Get user's achievement history
    user_achievements = [ua.achievement_id for ua in 
                        UserAchievement.query.filter_by(user_id=user.id).all()]
    
    # Achievement checks
    achievement_checks = [
        (1, lambda: user.completed_lessons == 1),  # First Steps
        (2, lambda: Pet.query.filter_by(user_id=user.id).first() is not None),  # Pet Parent
        (3, lambda: check_daily_lesson_count(user) >= 5),  # Quick Learner
        (4, lambda: count_user_stories(user) >= 10),  # Story Master
        (5, lambda: count_math_problems_solved(user) >= 50),  # Math Wizard
        (6, lambda: count_friends_helped(user) >= 5),  # Caring Friend
        (7, lambda: check_lesson_variety(user)),  # Explorer
        (8, lambda: user.streak_days >= 30)  # Champion
    ]
    
    for achievement_id, check_func in achievement_checks:
        if achievement_id not in user_achievements and check_func():
            award_achievement(user, achievement_id)
            achievements_to_award.append(achievement_id)
    
    return achievements_to_award

def check_daily_lesson_count(user):
    """Check how many lessons completed today"""
    today = datetime.now().date()
    # This would typically query a learning_sessions table
    return len([event for event in session.get('learning_events', [])
                if event['type'] == 'lesson_completed' and 
                datetime.fromisoformat(event['timestamp']).date() == today])

def count_user_stories(user):
    """Count stories created by user"""
    # This would typically query a stories table
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    return patterns.get('stories_created', 0)

def count_math_problems_solved(user):
    """Count math problems solved by user"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    return patterns.get('math_problems_solved', 0)

def count_friends_helped(user):
    """Count friends helped by user"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    return patterns.get('friends_helped', 0)

def check_lesson_variety(user):
    """Check if user has tried different types of lessons"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    lesson_types = patterns.get('lesson_types_tried', [])
    required_types = ['math', 'language', 'science', 'creative', 'social']
    return len(set(lesson_types) & set(required_types)) >= len(required_types)

def award_achievement(user, achievement_id):
    """Award achievement to user"""
    achievement = Achievement.query.get(achievement_id)
    if achievement:
        user_achievement = UserAchievement(
            user_id=user.id,
            achievement_id=achievement_id,
            earned_date=datetime.utcnow()
        )
        db.session.add(user_achievement)
        
        # Award points
        user.experience_points += achievement.points

def get_recent_achievements(user):
    """Get user's recent achievements"""
    recent = UserAchievement.query.filter_by(user_id=user.id)\
                .order_by(UserAchievement.earned_date.desc())\
                .limit(5).all()
    
    return [{
        'name': ua.achievement.name,
        'description': ua.achievement.description,
        'icon': ua.achievement.icon,
        'points': ua.achievement.points,
        'earned_date': ua.earned_date.isoformat()
    } for ua in recent]

def get_next_recommended_lesson(user):
    """Get next recommended lesson for user"""
    # Get lessons user hasn't completed
    completed_lesson_ids = get_completed_lesson_ids(user)
    
    available_lessons = Lesson.query.filter(
        ~Lesson.id.in_(completed_lesson_ids),
        Lesson.difficulty_level <= user.level + 1
    ).all()
    
    if not available_lessons:
        return None
    
    # Score lessons based on user preferences
    user_patterns = get_user_learning_patterns(user)
    scored_lessons = []
    
    for lesson in available_lessons:
        score = calculate_lesson_relevance_score(lesson, user_patterns)
        scored_lessons.append((lesson, score))
    
    # Return highest scoring lesson
    scored_lessons.sort(key=lambda x: x[1], reverse=True)
    best_lesson = scored_lessons[0][0]
    
    return {
        'id': best_lesson.id,
        'title': best_lesson.title,
        'description': best_lesson.description,
        'estimated_time': best_lesson.estimated_time
    }

def get_completed_lesson_ids(user):
    """Get IDs of lessons completed by user"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    history = patterns.get('performance_history', [])
    return [h['lesson_id'] for h in history]

def calculate_lesson_relevance_score(lesson, user_patterns):
    """Calculate how relevant a lesson is to the user"""
    score = 50  # Base score
    
    # Prefer lessons matching user's learning style
    preferences = user_patterns.get('preferences', {})
    
    if lesson.has_visuals and preferences.get('visual_preference', 0) > 0.7:
        score += 20
    
    if lesson.has_interactive_elements and preferences.get('kinesthetic_preference', 0) > 0.7:
        score += 20
    
    # Prefer appropriate difficulty
    recent_performance = user_patterns.get('recent_performance', 0.5)
    if recent_performance > 0.8 and lesson.difficulty == 'hard':
        score += 15
    elif recent_performance < 0.4 and lesson.difficulty == 'easy':
        score += 15
    elif lesson.difficulty == 'medium':
        score += 10
    
    # Prefer variety
    recent_types = get_recent_lesson_types(user_patterns)
    if lesson.content_type not in recent_types[-3:]:  # Not in last 3 lesson types
        score += 10
    
    return score

def get_recent_lesson_types(user_patterns):
    """Get recent lesson types completed by user"""
    history = user_patterns.get('performance_history', [])
    recent_lessons = history[-10:]  # Last 10 lessons
    
    lesson_types = []
    for record in recent_lessons:
        lesson = Lesson.query.get(record['lesson_id'])
        if lesson:
            lesson_types.append(lesson.content_type)
    
    return lesson_types

def generate_visual_aids(lesson):
    """Generate visual aids for visual learners"""
    visual_aids = []
    
    content_type = lesson.content_type
    
    if content_type == 'math':
        visual_aids = [
            {'type': 'diagram', 'title': 'Number Line', 'description': 'Visual number representation'},
            {'type': 'chart', 'title': 'Problem Breakdown', 'description': 'Step-by-step visual solution'},
            {'type': 'animation', 'title': 'Concept Animation', 'description': 'Animated explanation'}
        ]
    elif content_type == 'language':
        visual_aids = [
            {'type': 'word_cloud', 'title': 'Key Vocabulary', 'description': 'Important words visualized'},
            {'type': 'story_map', 'title': 'Story Structure', 'description': 'Visual story breakdown'},
            {'type': 'character_chart', 'title': 'Character Relationships', 'description': 'Visual character connections'}
        ]
    elif content_type == 'science':
        visual_aids = [
            {'type': 'experiment_diagram', 'title': 'Experiment Setup', 'description': 'Visual experiment guide'},
            {'type': 'process_flow', 'title': 'Scientific Process', 'description': 'Step-by-step process'},
            {'type': 'comparison_chart', 'title': 'Compare & Contrast', 'description': 'Visual comparisons'}
        ]
    
    return visual_aids

def generate_interactive_elements(lesson):
    """Generate interactive elements for kinesthetic learners"""
    interactive_elements = []
    
    content_type = lesson.content_type
    
    if content_type == 'math':
        interactive_elements = [
            {'type': 'drag_drop', 'title': 'Number Sorting', 'description': 'Drag numbers to solve'},
            {'type': 'calculator_game', 'title': 'Math Challenge', 'description': 'Interactive problem solving'},
            {'type': 'pattern_builder', 'title': 'Pattern Creator', 'description': 'Build mathematical patterns'}
        ]
    elif content_type == 'language':
        interactive_elements = [
            {'type': 'word_builder', 'title': 'Word Constructor', 'description': 'Build words from letters'},
            {'type': 'story_builder', 'title': 'Story Creator', 'description': 'Interactive story creation'},
            {'type': 'grammar_game', 'title': 'Grammar Adventure', 'description': 'Grammar through gameplay'}
        ]
    elif content_type == 'science':
        interactive_elements = [
            {'type': 'virtual_lab', 'title': 'Virtual Experiment', 'description': 'Hands-on virtual experiments'},
            {'type': 'simulation', 'title': 'Science Simulation', 'description': 'Interactive simulations'},
            {'type': 'hypothesis_tester', 'title': 'Hypothesis Lab', 'description': 'Test your theories'}
        ]
    
    return interactive_elements

def create_memory_cards(lesson):
    """Create memory game cards from lesson content"""
    content = json.loads(lesson.content) if lesson.content else {}
    cards = []
    
    # Extract key concepts for memory game
    if 'key_concepts' in content:
        concepts = content['key_concepts']
        for i, concept in enumerate(concepts):
            # Create pairs of cards (concept and definition)
            cards.append({
                'id': f'concept_{i}_1',
                'type': 'concept',
                'content': concept['term'],
                'match_id': f'concept_{i}'
            })
            cards.append({
                'id': f'concept_{i}_2',
                'type': 'definition',
                'content': concept['definition'],
                'match_id': f'concept_{i}'
            })
    
    # If no key concepts, create from lesson title and description
    if not cards:
        cards = [
            {'id': 'lesson_1', 'type': 'title', 'content': lesson.title, 'match_id': 'lesson'},
            {'id': 'lesson_2', 'type': 'description', 'content': lesson.description, 'match_id': 'lesson'}
        ]
    
    # Shuffle cards
    random.shuffle(cards)
    return cards

def identify_user_weaknesses(user):
    """Identify user's weak areas based on performance"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    history = patterns.get('performance_history', [])
    
    # Analyze performance by topic
    topic_performance = defaultdict(list)
    
    for record in history:
        lesson = Lesson.query.get(record['lesson_id'])
        if lesson:
            topic_performance[lesson.content_type].append(record['score'])
    
    weaknesses = []
    for topic, scores in topic_performance.items():
        avg_score = sum(scores) / len(scores)
        if avg_score < 60:  # Below 60% average
            weaknesses.append({
                'topic': topic,
                'average_score': avg_score,
                'attempts': len(scores)
            })
    
    # Sort by worst performance
    weaknesses.sort(key=lambda x: x['average_score'])
    return weaknesses

def identify_strengths(user):
    """Identify user's strong areas"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    history = patterns.get('performance_history', [])
    
    topic_performance = defaultdict(list)
    
    for record in history:
        lesson = Lesson.query.get(record['lesson_id'])
        if lesson:
            topic_performance[lesson.content_type].append(record['score'])
    
    strengths = []
    for topic, scores in topic_performance.items():
        avg_score = sum(scores) / len(scores)
        if avg_score >= 80:  # Above 80% average
            strengths.append({
                'topic': topic,
                'average_score': avg_score,
                'attempts': len(scores)
            })
    
    # Sort by best performance
    strengths.sort(key=lambda x: x['average_score'], reverse=True)
    return strengths

def get_performance_trends(user):
    """Get user's performance trends over time"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    history = patterns.get('performance_history', [])
    
    if len(history) < 2:
        return {'trend': 'insufficient_data'}
    
    # Group by date
    daily_performance = defaultdict(list)
    for record in history:
        date = datetime.fromisoformat(record['timestamp']).date()
        daily_performance[date].append(record['score'])
    
    # Calculate daily averages
    daily_averages = {}
    for date, scores in daily_performance.items():
        daily_averages[date] = sum(scores) / len(scores)
    
    # Calculate trend
    dates = sorted(daily_averages.keys())
    scores = [daily_averages[date] for date in dates]
    
    if len(scores) >= 2:
        # Simple linear trend
        x = list(range(len(scores)))
        trend_slope = statistics.correlation(x, scores) if len(scores) > 1 else 0
        
        return {
            'trend': 'improving' if trend_slope > 0.1 else 'declining' if trend_slope < -0.1 else 'stable',
            'slope': trend_slope,
            'daily_averages': {str(date): score for date, score in daily_averages.items()},
            'current_average': scores[-1] if scores else 0
        }
    
    return {'trend': 'insufficient_data'}

def get_detailed_learning_patterns(user):
    """Get detailed learning patterns analysis"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    
    detailed_patterns = {
        'preferred_difficulty': analyze_difficulty_preference(patterns),
        'learning_pace': analyze_learning_pace(patterns),
        'time_patterns': analyze_time_patterns(patterns),
        'content_preferences': analyze_content_preferences(patterns),
        'engagement_patterns': analyze_engagement_patterns(patterns)
    }
    
    return detailed_patterns

def analyze_difficulty_preference(patterns):
    """Analyze user's difficulty preference"""
    history = patterns.get('performance_history', [])
    
    difficulty_performance = defaultdict(list)
    for record in history:
        lesson = Lesson.query.get(record['lesson_id'])
        if lesson:
            difficulty_performance[lesson.difficulty].append(record['score'])
    
    preferences = {}
    for difficulty, scores in difficulty_performance.items():
        preferences[difficulty] = {
            'average_score': sum(scores) / len(scores),
            'attempts': len(scores),
            'success_rate': len([s for s in scores if s >= 70]) / len(scores)
        }
    
    return preferences

def analyze_learning_pace(patterns):
    """Analyze user's learning pace"""
    history = patterns.get('performance_history', [])
    
    if len(history) < 2:
        return {'pace': 'unknown'}
    
    # Calculate time between lessons
    timestamps = [datetime.fromisoformat(record['timestamp']) for record in history]
    timestamps.sort()
    
    intervals = []
    for i in range(1, len(timestamps)):
        interval = (timestamps[i] - timestamps[i-1]).total_seconds() / 3600  # hours
        intervals.append(interval)
    
    avg_interval = sum(intervals) / len(intervals)
    
    if avg_interval < 2:
        pace = 'very_fast'
    elif avg_interval < 24:
        pace = 'fast'
    elif avg_interval < 72:
        pace = 'moderate'
    else:
        pace = 'slow'
    
    return {
        'pace': pace,
        'average_interval_hours': avg_interval,
        'consistency': statistics.stdev(intervals) if len(intervals) > 1 else 0
    }

def analyze_time_patterns(patterns):
    """Analyze when user learns best"""
    history = patterns.get('performance_history', [])
    
    hour_performance = defaultdict(list)
    for record in history:
        hour = datetime.fromisoformat(record['timestamp']).hour
        hour_performance[hour].append(record['score'])
    
    best_hours = []
    for hour, scores in hour_performance.items():
        avg_score = sum(scores) / len(scores)
        if avg_score >= 75:  # Good performance threshold
            best_hours.append({'hour': hour, 'average_score': avg_score})
    
    best_hours.sort(key=lambda x: x['average_score'], reverse=True)
    
    return {
        'best_hours': best_hours[:3],  # Top 3 hours
        'hourly_performance': {str(hour): sum(scores)/len(scores) 
                             for hour, scores in hour_performance.items()}
    }

def analyze_content_preferences(patterns):
    """Analyze content type preferences"""
    history = patterns.get('performance_history', [])
    
    content_performance = defaultdict(list)
    for record in history:
        lesson = Lesson.query.get(record['lesson_id'])
        if lesson:
            content_performance[lesson.content_type].append(record['score'])
    
    preferences = {}
    for content_type, scores in content_performance.items():
        preferences[content_type] = {
            'average_score': sum(scores) / len(scores),
            'attempts': len(scores),
            'preference_score': (sum(scores) / len(scores)) * len(scores)  # Score weighted by frequency
        }
    
    return preferences

def analyze_engagement_patterns(patterns):
    """Analyze user engagement patterns"""
    history = patterns.get('performance_history', [])
    
    # Analyze session lengths and scores
    engagement_data = []
    for record in history:
        engagement_data.append({
            'score': record['score'],
            'timestamp': record['timestamp']
        })
    
    # Calculate engagement trends
    recent_scores = [record['score'] for record in history[-10:]]
    early_scores = [record['score'] for record in history[:10]]
    
    engagement_trend = 'stable'
    if len(recent_scores) > 0 and len(early_scores) > 0:
        recent_avg = sum(recent_scores) / len(recent_scores)
        early_avg = sum(early_scores) / len(early_scores)
        
        if recent_avg > early_avg + 10:
            engagement_trend = 'increasing'
        elif recent_avg < early_avg - 10:
            engagement_trend = 'decreasing'
    
    return {
        'trend': engagement_trend,
        'consistency': calculate_consistency(history),
        'peak_performance_periods': identify_peak_periods(history)
    }

def calculate_consistency(history):
    """Calculate learning consistency"""
    if len(history) < 2:
        return 0
    
    scores = [record['score'] for record in history]
    return 100 - (statistics.stdev(scores) if len(scores) > 1 else 0)

def identify_peak_periods(history):
    """Identify periods of peak performance"""
    if len(history) < 5:
        return []
    
    # Group by weeks
    weekly_performance = defaultdict(list)
    for record in history:
        week = datetime.fromisoformat(record['timestamp']).isocalendar()[1]
        weekly_performance[week].append(record['score'])
    
    peak_weeks = []
    for week, scores in weekly_performance.items():
        avg_score = sum(scores) / len(scores)
        if avg_score >= 85:  # High performance threshold
            peak_weeks.append({
                'week': week,
                'average_score': avg_score,
                'lessons_completed': len(scores)
            })
    
    return sorted(peak_weeks, key=lambda x: x['average_score'], reverse=True)

def get_recent_performance(learning_patterns):
    """Get recent performance average"""
    history = learning_patterns.get('performance_history', [])
    if not history:
        return 0.5
    
    recent = history[-5:]  # Last 5 performances
    scores = [p['score'] for p in recent]
    return sum(scores) / len(scores) / 100 if scores else 0.5

def make_question_easier(question):
    """Make a question easier"""
    # Add more obvious hints
    if 'hint' not in question:
        question['hint'] = "Think step by step!"
    
    # Reduce number of options if multiple choice
    if question.get('type') == 'multiple_choice' and len(question.get('options', [])) > 3:
        # Keep correct answer and 2 random wrong answers
        correct_idx = question.get('correct_answer', 0)
        options = question['options']
        correct_answer = options[correct_idx]
        
        wrong_answers = [opt for i, opt in enumerate(options) if i != correct_idx]
        selected_wrong = random.sample(wrong_answers, min(2, len(wrong_answers)))
        
        new_options = [correct_answer] + selected_wrong
        random.shuffle(new_options)
        
        question['options'] = new_options
        question['correct_answer'] = new_options.index(correct_answer)
    
    return question

def make_question_harder(question):
    """Make a question harder"""
    # Remove hints
    if 'hint' in question:
        del question['hint']
    
    # Add more complex options if multiple choice
    if question.get('type') == 'multiple_choice':
        # Add distractor answers
        additional_options = generate_distractors(question)
        if additional_options:
            question['options'].extend(additional_options)
    
    # Add time pressure
    question['time_limit'] = question.get('time_limit', 60) * 0.8  # 20% less time
    
    return question

def generate_distractors(question):
    """Generate distractor answers for multiple choice questions"""
    # This is a simplified implementation
    # In a real system, you'd use NLP to generate plausible wrong answers
    distractors = []
    
    topic = question.get('topic', '')
    if 'math' in topic.lower():
        # For math, generate close numerical answers
        if question.get('correct_answer_value'):
            correct = question['correct_answer_value']
            distractors = [
                str(correct + 1),
                str(correct - 1),
                str(correct * 2)
            ]
    
    return distractors[:2]  # Max 2 additional distractors

def calculate_learning_velocity(user):
    """Calculate how fast user is learning"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    history = patterns.get('performance_history', [])
    
    if len(history) < 3:
        return 0.5  # Average velocity
    
    # Calculate improvement rate over time
    recent_scores = [record['score'] for record in history[-5:]]
    early_scores = [record['score'] for record in history[:5]]
    
    recent_avg = sum(recent_scores) / len(recent_scores)
    early_avg = sum(early_scores) / len(early_scores)
    
    improvement = recent_avg - early_avg
    time_span = len(history)
    
    # Normalize velocity (improvement per lesson)
    velocity = improvement / time_span if time_span > 0 else 0
    
    # Convert to 0-1 scale
    return min(1.0, max(0.0, 0.5 + velocity / 100))

def get_preferred_learning_times(user):
    """Get user's preferred learning times"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    time_patterns = analyze_time_patterns(patterns)
    
    best_hours = time_patterns.get('best_hours', [])
    if not best_hours:
        return 'any time'
    
    # Convert hours to readable format
    hour_ranges = []
    for hour_data in best_hours:
        hour = hour_data['hour']
        if 6 <= hour < 12:
            hour_ranges.append('morning')
        elif 12 <= hour < 17:
            hour_ranges.append('afternoon')
        elif 17 <= hour < 21:
            hour_ranges.append('evening')
        else:
            hour_ranges.append('night')
    
    # Return most common time range
    if hour_ranges:
        return Counter(hour_ranges).most_common(1)[0][0]
    
    return 'any time'

def get_user_learning_profile(user):
    """Get comprehensive user learning profile for AI tutor"""
    patterns = get_user_learning_patterns(user)
    
    profile = {
        'level': user.level,
        'learning_style': patterns.get('preferences', {}).get('visual_preference', 0.5),
        'recent_performance': patterns.get('recent_performance', 0.5),
        'strengths': [s['topic'] for s in identify_strengths(user)],
        'weaknesses': [w['topic'] for w in identify_user_weaknesses(user)],
        'preferred_difficulty': patterns.get('preferences', {}).get('difficulty_preference', 0.5),
        'engagement_level': patterns.get('recent_performance', 0.5),
        'learning_pace': patterns.get('learning_velocity', 0.5)
    }
    
    return profile

def classify_question_type(question):
    """Classify the type of question asked"""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['how', 'explain', 'what is', 'define']):
        return 'explanation'
    elif any(word in question_lower for word in ['help', 'stuck', 'dont understand', "don't understand"]):
        return 'help_request'
    elif any(word in question_lower for word in ['example', 'show me', 'demonstrate']):
        return 'example_request'
    elif '?' in question:
        return 'question'
    else:
        return 'general'

def get_suggested_learning_actions(question):
    """Get suggested learning actions based on question"""
    question_type = classify_question_type(question)
    
    suggestions = {
        'explanation': [
            'Review related lesson materials',
            'Try practice exercises',
            'Watch explanatory videos'
        ],
        'help_request': [
            'Break down the problem into smaller steps',
            'Review prerequisites',
            'Ask for peer help'
        ],
        'example_request': [
            'Check lesson examples',
            'Try interactive simulations',
            'Create your own examples'
        ],
        'question': [
            'Research the topic',
            'Discuss with peers',
            'Consult additional resources'
        ],
        'general': [
            'Continue with current lesson',
            'Explore related topics',
            'Practice more exercises'
        ]
    }
    
    return suggestions.get(question_type, suggestions['general'])

def find_related_lessons(question):
    """Find lessons related to the question"""
    # Simple keyword matching - in a real system, you'd use semantic search
    keywords = extract_keywords(question)
    
    related_lessons = []
    lessons = Lesson.query.all()
    
    for lesson in lessons:
        lesson_text = f"{lesson.title} {lesson.description}".lower()
        
        # Check if any keywords appear in lesson
        matches = sum(1 for keyword in keywords if keyword in lesson_text)
        
        if matches > 0:
            related_lessons.append({
                'id': lesson.id,
                'title': lesson.title,
                'description': lesson.description,
                'relevance_score': matches
            })
    
    # Sort by relevance and return top 3
    related_lessons.sort(key=lambda x: x['relevance_score'], reverse=True)
    return related_lessons[:3]

@education_bp.route('/learn')
@login_required
def learn_dashboard():
    """Main learning dashboard with personalized content"""
    user_progress = {
        'total_lessons': Lesson.query.count(),
        'completed_lessons': current_user.completed_lessons,
        'current_level': current_user.level,
        'experience_points': current_user.experience_points,
        'streak_days': current_user.streak_days
    }
    
    # Get personalized lesson recommendations
    recommended_lessons = get_personalized_lessons(current_user)
    
    # Get user's pet status
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    pet_status = {
        'happiness': user_pet.happiness if user_pet else 50,
        'hunger': user_pet.hunger if user_pet else 50,
        'energy': user_pet.energy if user_pet else 50,
        'needs_attention': user_pet.happiness < 30 if user_pet else False
    }
    
    return render_template('learn_dashboard.html', 
                         progress=user_progress,
                         lessons=recommended_lessons,
                         pet_status=pet_status)

@education_bp.route('/lesson/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    """View specific lesson with adaptive content"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Adapt content based on user's learning style and performance
    adapted_content = adapt_lesson_content(lesson, current_user)
    
    # Track lesson start
    track_learning_event('lesson_started', lesson_id)
    
    return render_template('lesson_view.html', 
                         lesson=lesson,
                         adapted_content=adapted_content)

@education_bp.route('/lesson/<int:lesson_id>/complete', methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    """Complete lesson and update user progress"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.get_json()
    
    score = data.get('score', 0)
    time_spent = data.get('time_spent', 0)
    answers = data.get('answers', [])
    
    # Analyze user's performance for personalization
    performance_analysis = analyze_lesson_performance(answers, time_spent, score)
    
    # Update user progress
    current_user.completed_lessons += 1
    current_user.experience_points += calculate_experience_points(score, time_spent)
    current_user.total_study_time += time_spent
    
    # Update learning patterns for AI personalization
    update_learning_patterns(current_user, lesson, performance_analysis)
    
    # Check for level up
    if check_level_up(current_user):
        current_user.level += 1
        unlock_new_content(current_user)
    
    # Update pet happiness based on learning
    update_pet_from_learning(current_user, score)
    
    # Check for achievements
    check_and_award_achievements(current_user, lesson, score)
    
    db.session.commit()
    
    # Track completion
    track_learning_event('lesson_completed', lesson_id, {
        'score': score,
        'time_spent': time_spent,
        'performance_level': performance_analysis['level']
    })
    
    return jsonify({
        'success': True,
        'experience_gained': calculate_experience_points(score, time_spent),
        'new_level': current_user.level,
        'achievements': get_recent_achievements(current_user),
        'pet_reaction': get_pet_reaction(score),
        'next_lesson': get_next_recommended_lesson(current_user)
    })

@education_bp.route('/adaptive-quiz/<int:lesson_id>')
@login_required
def adaptive_quiz(lesson_id):
    """Generate adaptive quiz based on user's learning patterns"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Get user's learning patterns
    learning_patterns = get_user_learning_patterns(current_user)
    
    # Generate adaptive questions
    quiz_questions = generate_adaptive_questions(lesson, learning_patterns)
    
    return render_template('adaptive_quiz.html',
                         lesson=lesson,
                         questions=quiz_questions)

@education_bp.route('/memory-game/<int:lesson_id>')
@login_required
def memory_game(lesson_id):
    """Interactive memory game for lesson content"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Create memory game cards from lesson content
    memory_cards = create_memory_cards(lesson)
    
    return render_template('memory_game.html',
                         lesson=lesson,
                         cards=memory_cards)

@education_bp.route('/practice-mode')
@login_required
def practice_mode():
    """Practice mode with AI-generated content"""
    user_weaknesses = identify_user_weaknesses(current_user)
    practice_content = generate_practice_content(user_weaknesses)
    
    return render_template('practice_mode.html',
                         practice_content=practice_content)

@education_bp.route('/learning-analytics')
@login_required
def learning_analytics():
    """Detailed learning analytics dashboard"""
    analytics = {
        'performance_trends': get_performance_trends(current_user),
        'learning_patterns': get_detailed_learning_patterns(current_user),
        'strength_areas': _identify_strengths(current_user),
        'improvement_areas': identify_user_weaknesses(current_user),
        'recommended_actions': get_learning_recommendations(current_user)
    }
    
    return render_template('learning_analytics.html', analytics=analytics)

@education_bp.route('/ai-tutor-chat', methods=['POST'])
@login_required
def ai_tutor_chat():
    """AI tutor chat for personalized help"""
    data = request.get_json()
    question = data.get('question', '')
    context = data.get('context', '')
    
    # Analyze question sentiment and urgency
    sentiment = sentiment_service.analyze_sentiment(question)
    
    # Generate personalized response
    response = llm_service.generate_tutor_response(
        question=question,
        user_profile=get_user_learning_profile(current_user),
        context=context,
        sentiment=sentiment
    )
    
    # Track interaction for learning
    track_learning_event('ai_tutor_interaction', None, {
        'question_type': classify_question_type(question),
        'sentiment': sentiment,
        'response_helpful': None  # Will be updated by user feedback
    })
    
    return jsonify({
        'response': response,
        'suggested_actions': get_suggested_learning_actions(question),
        'related_lessons': find_related_lessons(question)
    })

# Helper functions for personalization and real-time learning

def extract_keywords(text):
    """Extract keywords from text"""
    # Simple keyword extraction - remove common words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
                   'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 
                   'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
                   'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    
    # Clean and split text
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    keywords = [word for word in words if word not in common_words and len(word) > 2]
    
    return list(set(keywords))

def classify_question_type(question):
    """Classify the type of question asked"""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['what', 'define', 'explain', 'meaning']):
        return 'definition'
    elif any(word in question_lower for word in ['how', 'steps', 'process', 'method']):
        return 'procedure'
    elif any(word in question_lower for word in ['why', 'reason', 'because', 'cause']):
        return 'explanation'
    elif any(word in question_lower for word in ['when', 'time', 'date', 'period']):
        return 'temporal'
    elif any(word in question_lower for word in ['where', 'location', 'place']):
        return 'location'
    elif any(word in question_lower for word in ['calculate', 'solve', 'find', 'compute']):
        return 'problem_solving'
    elif any(word in question_lower in ['help', 'stuck', 'confused', 'don\'t understand']):
        return 'help_request'
    else:
        return 'general'

def get_suggested_learning_actions(question):
    """Get suggested learning actions based on question"""
    question_type = classify_question_type(question)
    
    suggestions = {
        'definition': [
            'Review glossary terms',
            'Watch introductory videos',
            'Practice with flashcards'
        ],
        'procedure': [
            'Follow step-by-step tutorials',
            'Practice with guided exercises',
            'Watch demonstration videos'
        ],
        'explanation': [
            'Read detailed explanations',
            'Explore cause-and-effect relationships',
            'Discuss with study groups'
        ],
        'problem_solving': [
            'Practice similar problems',
            'Review solution strategies',
            'Use interactive problem solvers'
        ],
        'help_request': [
            'Schedule one-on-one tutoring',
            'Join study groups',
            'Review prerequisite materials'
        ],
        'general': [
            'Explore related topics',
            'Take practice quizzes',
            'Review recent lessons'
        ]
    }
    
    return suggestions.get(question_type, suggestions['general'])

def find_related_lessons(question):
    """Find lessons related to the question"""
    keywords = extract_keywords(question)
    related_lessons = []
    lessons = Lesson.query.all()
    
    for lesson in lessons:
        lesson_text = f"{lesson.title} {lesson.description}".lower()
        if hasattr(lesson, 'content') and lesson.content:
            lesson_text += f" {lesson.content}".lower()
        
        # Check if any keywords appear in lesson
        matches = sum(1 for keyword in keywords if keyword in lesson_text)
        if matches > 0:
            related_lessons.append({
                'id': lesson.id,
                'title': lesson.title,
                'description': lesson.description,
                'relevance_score': matches
            })
    
    # Sort by relevance and return top 3
    related_lessons.sort(key=lambda x: x['relevance_score'], reverse=True)
    return related_lessons[:3]

def get_user_learning_profile(user):
    """Get comprehensive user learning profile for AI tutor"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    
    profile = {
        'level': user.level,
        'learning_style': patterns.get('preferences', {}).get('visual_preference', 0.5),
        'recent_performance': calculate_recent_performance(user),
        'strengths': identify_strengths(user),
        'weaknesses': identify_user_weaknesses(user),
        'preferred_difficulty': patterns.get('preferences', {}).get('difficulty_preference', 0.5),
        'engagement_level': calculate_engagement_level(user),
        'learning_goals': get_user_goals(user)
    }
    
    return profile

def calculate_lesson_relevance_score(lesson, user_patterns):
    """Calculate how relevant a lesson is for a user"""
    score = 0
    
    # Base score from lesson difficulty matching user level
    difficulty_match = 1 - abs(lesson.difficulty_level - user_patterns.get('current_level', 1)) / 5
    score += difficulty_match * 30
    
    # Score based on learning style preferences
    preferences = user_patterns.get('preferences', {})
    if lesson.has_visuals and preferences.get('visual_preference', 0) > 0.5:
        score += 20
    if lesson.has_interactive_elements and preferences.get('kinesthetic_preference', 0) > 0.5:
        score += 20
    if lesson.has_audio and preferences.get('auditory_preference', 0) > 0.5:
        score += 20
    
    # Score based on user's weak areas
    weaknesses = user_patterns.get('weakness_areas', [])
    if hasattr(lesson, 'topics'):
        lesson_topics = json.loads(lesson.topics) if lesson.topics else []
        if any(topic in weaknesses for topic in lesson_topics):
            score += 25
    
    return min(100, score)

def generate_visual_aids(lesson):
    """Generate visual aids for visual learners"""
    visual_aids = []
    
    # Generate based on lesson content type
    if hasattr(lesson, 'content_type'):
        if lesson.content_type == 'math':
            visual_aids.extend([
                {'type': 'diagram', 'description': 'Number line visualization'},
                {'type': 'chart', 'description': 'Problem-solving flowchart'},
                {'type': 'infographic', 'description': 'Math concept summary'}
            ])
        elif lesson.content_type == 'science':
            visual_aids.extend([
                {'type': 'diagram', 'description': 'Process diagram'},
                {'type': 'illustration', 'description': 'Scientific concept illustration'},
                {'type': 'animation', 'description': 'Interactive simulation'}
            ])
        elif lesson.content_type == 'language':
            visual_aids.extend([
                {'type': 'word_cloud', 'description': 'Key vocabulary visualization'},
                {'type': 'story_map', 'description': 'Story structure diagram'},
                {'type': 'character_chart', 'description': 'Character relationship map'}
            ])
    
    return visual_aids

def generate_interactive_elements(lesson):
    """Generate interactive elements for kinesthetic learners"""
    interactive_elements = []
    
    if hasattr(lesson, 'content_type'):
        if lesson.content_type == 'math':
            interactive_elements.extend([
                {'type': 'drag_drop', 'description': 'Drag numbers to solve equations'},
                {'type': 'puzzle', 'description': 'Math puzzle game'},
                {'type': 'builder', 'description': 'Build shapes and patterns'}
            ])
        elif lesson.content_type == 'science':
            interactive_elements.extend([
                {'type': 'experiment', 'description': 'Virtual lab experiment'},
                {'type': 'simulation', 'description': 'Interactive simulation'},
                {'type': 'quiz_game', 'description': 'Science trivia game'}
            ])
        elif lesson.content_type == 'language':
            interactive_elements.extend([
                {'type': 'word_game', 'description': 'Interactive word building'},
                {'type': 'story_builder', 'description': 'Create your own story'},
                {'type': 'role_play', 'description': 'Character dialogue practice'}
            ])
    
    return interactive_elements

def check_level_up(user):
    """Check if user should level up"""
    # Level up criteria: enough experience points and lessons completed
    required_xp = user.level * 100  # Each level requires more XP
    required_lessons = user.level * 5  # Each level requires more lessons
    
    return (user.experience_points >= required_xp and 
            user.completed_lessons >= required_lessons)

def unlock_new_content(user):
    """Unlock new content when user levels up"""
    # Mark new lessons as available
    new_lessons = Lesson.query.filter(
        Lesson.difficulty_level <= user.level,
        Lesson.required_level <= user.level
    ).all()
    
    # You might want to create a UserUnlockedContent table
    # For now, we'll just log it
    logger.info(f"User {user.id} leveled up to {user.level}, unlocked {len(new_lessons)} lessons")

def check_and_award_achievements(user, lesson, score):
    """Check and award achievements based on performance"""
    achievements_to_award = []
    
    # First lesson achievement
    if user.completed_lessons == 1:
        achievements_to_award.append('First Steps')
    
    # Perfect score achievement
    if score == 100:
        achievements_to_award.append('Perfect Score')
    
    # Quick learner (5 lessons in one day)
    today = datetime.utcnow().date()
    today_lessons = LearningSession.query.filter(
        LearningSession.user_id == user.id,
        LearningSession.timestamp >= today,
        LearningSession.action == 'lesson_completed'
    ).count()
    
    if today_lessons >= 5:
        achievements_to_award.append('Quick Learner')
    
    # Award achievements
    for achievement_name in achievements_to_award:
        achievement = Achievement.query.filter_by(name=achievement_name).first()
        if achievement:
            # Check if user already has this achievement
            existing = UserAchievement.query.filter_by(
                user_id=user.id, 
                achievement_id=achievement.id
            ).first()
            
            if not existing:
                user_achievement = UserAchievement(
                    user_id=user.id,
                    achievement_id=achievement.id,
                    earned_date=datetime.utcnow()
                )
                db.session.add(user_achievement)

def get_recent_achievements(user):
    """Get user's recent achievements"""
    recent = UserAchievement.query.filter_by(user_id=user.id)\
        .order_by(UserAchievement.earned_date.desc())\
        .limit(3).all()
    
    return [{
        'name': ua.achievement.name,
        'description': ua.achievement.description,
        'icon': ua.achievement.icon,
        'earned_date': ua.earned_date
    } for ua in recent]

def get_next_recommended_lesson(user):
    """Get next recommended lesson for user"""
    recommended = get_personalized_lessons(user)
    if recommended:
        lesson = recommended[0]
        return {
            'id': lesson.id,
            'title': lesson.title,
            'description': lesson.description,
            'estimated_time': lesson.estimated_time
        }
    return None

def create_memory_cards(lesson):
    """Create memory game cards from lesson content"""
    cards = []
    
    # Extract key terms and definitions from lesson
    if hasattr(lesson, 'content') and lesson.content:
        content = json.loads(lesson.content) if isinstance(lesson.content, str) else lesson.content
        
        # Create pairs of cards from vocabulary or key concepts
        if 'vocabulary' in content:
            for term, definition in content['vocabulary'].items():
                cards.extend([
                    {'id': f"term_{len(cards)}", 'content': term, 'type': 'term'},
                    {'id': f"def_{len(cards)}", 'content': definition, 'type': 'definition'}
                ])
        
        # Create pairs from Q&A
        if 'questions' in content:
            for qa in content['questions'][:5]:  # Limit to 5 pairs
                cards.extend([
                    {'id': f"q_{len(cards)}", 'content': qa['question'], 'type': 'question'},
                    {'id': f"a_{len(cards)}", 'content': qa['answer'], 'type': 'answer'}
                ])
    
    # Shuffle cards
    random.shuffle(cards)
    return cards

def identify_user_weaknesses(user):
    """Identify areas where user needs improvement"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    performance_history = patterns.get('performance_history', [])
    
    if not performance_history:
        return []
    
    # Analyze performance by topic
    topic_performance = {}
    for record in performance_history:
        topics = record.get('topics', ['general'])
        score = record.get('score', 0)
        
        for topic in topics:
            if topic not in topic_performance:
                topic_performance[topic] = []
            topic_performance[topic].append(score)
    
    # Identify weak areas (average score < 60)
    weaknesses = []
    for topic, scores in topic_performance.items():
        avg_score = sum(scores) / len(scores)
        if avg_score < 60:
            weaknesses.append(topic)
    
    return weaknesses

def identify_strengths(user):
    """Identify user's strength areas"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    performance_history = patterns.get('performance_history', [])
    
    if not performance_history:
        return []
    
    # Analyze performance by topic
    topic_performance = {}
    for record in performance_history:
        topics = record.get('topics', ['general'])
        score = record.get('score', 0)
        
        for topic in topics:
            if topic not in topic_performance:
                topic_performance[topic] = []
            topic_performance[topic].append(score)
    
    # Identify strong areas (average score > 80)
    strengths = []
    for topic, scores in topic_performance.items():
        avg_score = sum(scores) / len(scores)
        if avg_score > 80:
            strengths.append(topic)
    
    return strengths

def get_performance_trends(user):
    """Get user's performance trends over time"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    performance_history = patterns.get('performance_history', [])
    
    if not performance_history:
        return {'trend': 'stable', 'data': []}
    
    # Group by week
    weekly_performance = {}
    for record in performance_history:
        date = datetime.fromisoformat(record['timestamp']).date()
        week = date.isocalendar()[1]  # Week number
        
        if week not in weekly_performance:
            weekly_performance[week] = []
        weekly_performance[week].append(record['score'])
    
    # Calculate weekly averages
    trends = []
    for week in sorted(weekly_performance.keys()):
        avg_score = sum(weekly_performance[week]) / len(weekly_performance[week])
        trends.append({'week': week, 'score': avg_score})
    
    # Determine overall trend
    if len(trends) >= 2:
        if trends[-1]['score'] > trends[0]['score']:
            trend = 'improving'
        elif trends[-1]['score'] < trends[0]['score']:
            trend = 'declining'
        else:
            trend = 'stable'
    else:
        trend = 'stable'
    
    return {'trend': trend, 'data': trends}

def get_detailed_learning_patterns(user):
    """Get detailed learning patterns"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    
    return {
        'learning_style': patterns.get('preferences', {}),
        'study_habits': get_study_habits(user),
        'preferred_content_types': get_preferred_content_types(user),
        'optimal_session_length': calculate_optimal_session_length(user),
        'best_performance_times': get_preferred_learning_times(user)
    }

def get_study_habits(user):
    """Analyze user's study habits"""
    # This would analyze learning session patterns
    return {
        'consistency': 'regular',  # regular, irregular, sporadic
        'session_frequency': 'daily',  # daily, weekly, occasional
        'preferred_session_length': '15-30 minutes'
    }

def get_preferred_content_types(user):
    """Get user's preferred content types"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    performance_history = patterns.get('performance_history', [])
    
    content_type_scores = {}
    for record in performance_history:
        content_type = record.get('content_type', 'general')
        score = record.get('score', 0)
        
        if content_type not in content_type_scores:
            content_type_scores[content_type] = []
        content_type_scores[content_type].append(score)
    
    # Calculate average scores and rank
    preferences = []
    for content_type, scores in content_type_scores.items():
        avg_score = sum(scores) / len(scores)
        preferences.append({
            'type': content_type,
            'performance': avg_score,
            'engagement': len(scores)
        })
    
    return sorted(preferences, key=lambda x: x['performance'], reverse=True)

def calculate_optimal_session_length(user):
    """Calculate optimal learning session length for user"""
    # This would analyze performance vs session length
    # For now, return a default based on age/level
    if user.level <= 3:
        return 15  # minutes
    elif user.level <= 6:
        return 25
    else:
        return 35

def get_preferred_learning_times(user):
    """Get user's preferred learning times"""
    # This would analyze when user performs best
    # For now, return common patterns
    return ['morning', 'afternoon']

def calculate_engagement_level(user):
    """Calculate user engagement level"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    
    # Factors: session frequency, completion rate, time spent
    recent_sessions = len(patterns.get('performance_history', [])[-7:])  # Last 7 sessions
    
    if recent_sessions >= 5:
        return 'high'
    elif recent_sessions >= 3:
        return 'medium'
    else:
        return 'low'

def get_user_goals(user):
    """Get user's learning goals"""
    # This would typically be stored in user preferences
    # For now, return default goals based on level
    if user.level <= 3:
        return ['master_basics', 'build_confidence']
    elif user.level <= 6:
        return ['expand_knowledge', 'improve_speed']
    else:
        return ['advanced_topics', 'prepare_for_tests']

def calculate_learning_velocity(user):
    """Calculate how quickly user learns new concepts"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    performance_history = patterns.get('performance_history', [])
    
    if len(performance_history) < 2:
        return 'average'
    
    # Look at improvement rate over time
    early_scores = [p['score'] for p in performance_history[:5]]
    recent_scores = [p['score'] for p in performance_history[-5:]]
    
    early_avg = sum(early_scores) / len(early_scores) if early_scores else 0
    recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
    
    improvement = recent_avg - early_avg
    
    if improvement > 20:
        return 'fast'
    elif improvement > 10:
        return 'average'
    else:
        return 'steady'

def get_recent_performance(learning_patterns):
    """Get recent performance from learning patterns"""
    performance_history = learning_patterns.get('performance_history', [])
    if not performance_history:
        return 0.5
    
    # Get last 5 performances
    recent = performance_history[-5:]
    scores = [p.get('score', 0) for p in recent]
    
    return sum(scores) / len(scores) / 100 if scores else 0.5

def make_question_easier(question):
    """Make a question easier for struggling students"""
    # Add hints, reduce options, simplify language
    question_copy = question.copy()
    
    # Add hint if not present
    if 'hint' not in question_copy:
        question_copy['hint'] = "Think step by step and take your time!"
    
    # Reduce multiple choice options if applicable
    if 'options' in question_copy and len(question_copy['options']) > 3:
        # Keep correct answer and reduce incorrect options
        correct_index = question_copy.get('correct_answer', 0)
        correct_option = question_copy['options'][correct_index]
        
        # Keep 2 incorrect options
        incorrect_options = [opt for i, opt in enumerate(question_copy['options']) if i != correct_index]
        reduced_options = [correct_option] + incorrect_options[:2]
        
        random.shuffle(reduced_options)
        question_copy['options'] = reduced_options
        question_copy['correct_answer'] = reduced_options.index(correct_option)
    
    return question_copy

def make_question_harder(question):
    """Make a question harder for advanced students"""
    question_copy = question.copy()
    
    # Remove hints
    if 'hint' in question_copy:
        del question_copy['hint']
    
    # Add time pressure
    question_copy['time_limit'] = 30  # seconds
    
    # Make language more complex or add additional steps
    if 'bonus_challenge' not in question_copy:
        question_copy['bonus_challenge'] = "Can you explain why this is the correct answer?"
    
    return question_copy

def get_personalized_lessons(user):
    """Get personalized lesson recommendations based on user's learning patterns"""
    user_patterns = get_user_learning_patterns(user)
    
    # Get lessons matching user's level and interests
    base_lessons = Lesson.query.filter(
        Lesson.difficulty_level <= user.level + 1,
        Lesson.difficulty_level >= max(1, user.level - 1)
    ).all()
    
    # Score lessons based on user patterns
    scored_lessons = []
    for lesson in base_lessons:
        score = calculate_lesson_relevance_score(lesson, user_patterns)
        scored_lessons.append((lesson, score))
    
    # Sort by relevance score
    scored_lessons.sort(key=lambda x: x[1], reverse=True)
    
    return [lesson for lesson, score in scored_lessons[:10]]

def adapt_lesson_content(lesson, user):
    """Adapt lesson content based on user's learning style"""
    user_patterns = get_user_learning_patterns(user)
    
    adapted_content = {
        'content': lesson.content,
        'visual_aids': [],
        'interactive_elements': [],
        'difficulty_adjustments': {}
    }
    
    # Adjust for visual learners
    if user_patterns.get('visual_preference', 0) > 0.7:
        adapted_content['visual_aids'] = generate_visual_aids(lesson)
    
    # Adjust for kinesthetic learners
    if user_patterns.get('kinesthetic_preference', 0) > 0.7:
        adapted_content['interactive_elements'] = generate_interactive_elements(lesson)
    
    # Adjust difficulty based on recent performance
    recent_performance = user_patterns.get('recent_performance', 0.5)
    if recent_performance < 0.4:
        adapted_content['difficulty_adjustments']['easier'] = True
    elif recent_performance > 0.8:
        adapted_content['difficulty_adjustments']['harder'] = True
    
    return adapted_content

def analyze_lesson_performance(answers, time_spent, score):
    """Analyze user's performance for personalization"""
    analysis = {
        'level': 'average',
        'learning_style_indicators': {},
        'difficulty_areas': [],
        'strengths': []
    }
    
    # Analyze performance level
    if score >= 90:
        analysis['level'] = 'excellent'
    elif score >= 70:
        analysis['level'] = 'good'
    elif score >= 50:
        analysis['level'] = 'average'
    else:
        analysis['level'] = 'needs_improvement'
    
    # Analyze time spent vs score for learning style
    efficiency_ratio = score / max(time_spent, 1)
    if efficiency_ratio > 1.5:
        analysis['learning_style_indicators']['quick_learner'] = True
    elif efficiency_ratio < 0.5:
        analysis['learning_style_indicators']['needs_more_time'] = True
    
    # Analyze answer patterns
    for i, answer in enumerate(answers):
        if answer.get('correct', False):
            analysis['strengths'].append(answer.get('topic', f'question_{i}'))
        else:
            analysis['difficulty_areas'].append(answer.get('topic', f'question_{i}'))
    
    return analysis

def update_learning_patterns(user, lesson, performance_analysis):
    """Update user's learning patterns based on performance"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    
    # Update performance history
    if 'performance_history' not in patterns:
        patterns['performance_history'] = []
    
    patterns['performance_history'].append({
        'lesson_id': lesson.id,
        'score': performance_analysis.get('score', 0),
        'level': performance_analysis['level'],
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Keep only last 50 records
    patterns['performance_history'] = patterns['performance_history'][-50:]
    
    # Update learning preferences
    update_learning_preferences(patterns, performance_analysis)
    
    user.learning_patterns = json.dumps(patterns)

def update_learning_preferences(patterns, performance_analysis):
    """Update learning preferences based on performance"""
    if 'preferences' not in patterns:
        patterns['preferences'] = {
            'visual_preference': 0.5,
            'kinesthetic_preference': 0.5,
            'difficulty_preference': 0.5
        }
    
    # Adjust preferences based on performance indicators
    for indicator, value in performance_analysis.get('learning_style_indicators', {}).items():
        if indicator == 'quick_learner' and value:
            patterns['preferences']['difficulty_preference'] = min(1.0, 
                patterns['preferences']['difficulty_preference'] + 0.1)
        elif indicator == 'needs_more_time' and value:
            patterns['preferences']['difficulty_preference'] = max(0.0,
                patterns['preferences']['difficulty_preference'] - 0.1)

def calculate_experience_points(score, time_spent):
    """Calculate experience points based on score and engagement"""
    base_points = score
    
    # Bonus for time spent (engagement)
    time_bonus = min(20, time_spent // 60)  # 1 point per minute, max 20
    
    # Bonus for perfect scores
    perfect_bonus = 50 if score == 100 else 0
    
    return base_points + time_bonus + perfect_bonus

def update_pet_from_learning(user, score):
    """Update pet happiness based on learning performance"""
    pet = Pet.query.filter_by(user_id=user.id).first()
    if pet:
        # Increase happiness based on score
        happiness_increase = score // 10  # 1 point per 10% score
        pet.happiness = min(100, pet.happiness + happiness_increase)
        
        # Decrease hunger slightly (learning makes pet happy, less hungry)
        pet.hunger = max(0, pet.hunger - 5)
        
        # Update last interaction
        pet.last_interaction = datetime.utcnow()

def get_pet_reaction(score):
    """Get pet reaction based on learning score"""
    if score >= 90:
        return {
            'emotion': 'ecstatic',
            'message': "Wow! Your pet is jumping with joy! 🎉",
            'animation': 'celebration'
        }
    elif score >= 70:
        return {
            'emotion': 'happy',
            'message': "Your pet is so proud of you! 😊",
            'animation': 'happy_dance'
        }
    elif score >= 50:
        return {
            'emotion': 'encouraging',
            'message': "Your pet believes in you! Keep going! 💪",
            'animation': 'encouraging'
        }
    else:
        return {
            'emotion': 'supportive',
            'message': "Your pet is here to help you learn! 🤗",
            'animation': 'supportive_hug'
        }

def generate_adaptive_questions(lesson, learning_patterns):
    """Generate adaptive questions based on learning patterns"""
    base_questions = json.loads(lesson.quiz_questions) if lesson.quiz_questions else []
    
    # Adapt questions based on user's recent performance
    recent_performance = get_recent_performance(learning_patterns)
    
    adapted_questions = []
    for question in base_questions:
        adapted_question = question.copy()
        
        # Adjust difficulty
        if recent_performance < 0.4:
            adapted_question = make_question_easier(adapted_question)
        elif recent_performance > 0.8:
            adapted_question = make_question_harder(adapted_question)
        
        adapted_questions.append(adapted_question)
    
    return adapted_questions

def track_learning_event(event_type, lesson_id, additional_data=None):
    """Track learning events for real-time adaptation"""
    # This would typically store in a separate analytics table
    # For now, we'll use session storage
    if 'learning_events' not in session:
        session['learning_events'] = []
    
    event = {
        'type': event_type,
        'lesson_id': lesson_id,
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': current_user.id,
        'data': additional_data or {}
    }
    
    session['learning_events'].append(event)
    
    # Keep only last 100 events
    session['learning_events'] = session['learning_events'][-100:]

def get_user_learning_patterns(user):
    """Get comprehensive user learning patterns"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    
    # Add computed patterns
    patterns['recent_performance'] = calculate_recent_performance(user)
    patterns['learning_velocity'] = calculate_learning_velocity(user)
    patterns['preferred_times'] = get_preferred_learning_times(user)
    
    return patterns

def calculate_recent_performance(user):
    """Calculate recent performance average"""
    patterns = json.loads(user.learning_patterns) if user.learning_patterns else {}
    history = patterns.get('performance_history', [])
    
    if not history:
        return 0.5
    
    # Get last 10 performances
    recent = history[-10:]
    scores = [p.get('score', 0) for p in recent]
    
    return sum(scores) / len(scores) / 100 if scores else 0.5

def generate_practice_content(weaknesses):
    """Generate practice content for identified weaknesses"""
    practice_content = []
    
    for weakness in weaknesses:
        content = {
            'topic': weakness,
            'exercises': llm_service.generate_practice_exercises(weakness),
            'explanations': llm_service.generate_explanations(weakness),
            'difficulty_levels': ['easy', 'medium', 'hard']
        }
        practice_content.append(content)
    
    return practice_content

def get_learning_recommendations(user):
    """Get personalized learning recommendations"""
    patterns = get_user_learning_patterns(user)
    
    recommendations = []
    
    # Time-based recommendations
    if patterns.get('preferred_times'):
        recommendations.append({
            'type': 'timing',
            'message': f"You learn best during {patterns['preferred_times']}",
            'action': 'Schedule study sessions during peak times'
        })
    
    # Performance-based recommendations
    recent_performance = patterns.get('recent_performance', 0.5)
    if recent_performance < 0.4:
        recommendations.append({
            'type': 'difficulty',
            'message': 'Consider reviewing basics before moving to advanced topics',
            'action': 'Take remedial lessons'
        })
    
    return recommendations