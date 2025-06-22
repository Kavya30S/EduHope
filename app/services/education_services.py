# Complete implementations for all missing functions in education.py

import json
import random
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

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

