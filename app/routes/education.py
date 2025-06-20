from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
from app.models.lesson import Lesson
from app.models.user import User
from app.models.achievement import Achievement
from app.models.pet import Pet
from app.models.emotion import EmotionData
from app.services.llm_service import LLMService
from app.services.sentiment_service import SentimentService
from app.database import db
import random
import json
from datetime import datetime

education_bp = Blueprint('education', __name__)
llm_service = LLMService()
sentiment_service = SentimentService()

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
        'strength_areas': identify_strengths(current_user),
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