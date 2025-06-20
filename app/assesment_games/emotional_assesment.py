from flask import Blueprint, render_template, request, jsonify, session
from app.models.user import User
from app.models.emotion import EmotionLog
from app.services.emotion_ai_services import EmotionAIService
from app.services.realtime_ai_services import RealtimeAIService
from app import db
import json
import random
from datetime import datetime

emotional_assessment_bp = Blueprint('emotional_assessment', __name__)
emotion_ai = EmotionAIService()
realtime_ai = RealtimeAIService()

class EmotionalAssessmentGame:
    def __init__(self):
        self.scenarios = self.load_emotion_scenarios()
        self.fantasy_characters = self.load_fantasy_characters()
        
    def load_emotion_scenarios(self):
        """Load age-appropriate emotional scenarios for children"""
        return [
            {
                'id': 'friendship_conflict',
                'title': '🌟 The Magic Friendship Garden',
                'scenario': 'In the enchanted friendship garden, two fairy friends had a disagreement about which flowers to plant. How do you think they should solve this?',
                'options': [
                    {'text': 'Talk and listen to each other', 'emotion_indicators': ['empathy', 'cooperation'], 'points': 10},
                    {'text': 'Ask the wise garden owl for help', 'emotion_indicators': ['seeking_help', 'wisdom'], 'points': 8},
                    {'text': 'Plant both types of flowers together', 'emotion_indicators': ['compromise', 'creativity'], 'points': 9},
                    {'text': 'Take turns choosing flowers each day', 'emotion_indicators': ['fairness', 'patience'], 'points': 8}
                ],
                'learning_objectives': ['conflict_resolution', 'empathy', 'communication']
            },
            {
                'id': 'fear_management',
                'title': '🦄 The Brave Little Unicorn',
                'scenario': 'A little unicorn is afraid of the dark forest but needs to help a lost butterfly. What would help the unicorn feel braver?',
                'options': [
                    {'text': 'Take a magical glowing friend along', 'emotion_indicators': ['seeking_support', 'courage'], 'points': 9},
                    {'text': 'Practice deep breathing like a dragon', 'emotion_indicators': ['self_regulation', 'coping_skills'], 'points': 10},
                    {'text': 'Remember all the brave things done before', 'emotion_indicators': ['self_confidence', 'reflection'], 'points': 8},
                    {'text': 'Sing a happy song while walking', 'emotion_indicators': ['positive_coping', 'joy'], 'points': 7}
                ],
                'learning_objectives': ['fear_management', 'courage', 'coping_strategies']
            },
            {
                'id': 'sadness_support',
                'title': '🐉 The Dragon's Rainy Day',
                'scenario': 'A young dragon feels sad because it rained and cancelled the sky parade. What could help the dragon feel better?',
                'options': [
                    {'text': 'Plan an indoor treasure hunt instead', 'emotion_indicators': ['adaptability', 'creativity'], 'points': 9},
                    {'text': 'Talk to dragon mom about feelings', 'emotion_indicators': ['communication', 'seeking_support'], 'points': 10},
                    {'text': 'Draw pictures of the sky parade', 'emotion_indicators': ['creative_expression', 'processing'], 'points': 8},
                    {'text': 'Help other dragons who are also sad', 'emotion_indicators': ['empathy', 'altruism'], 'points': 9}
                ],
                'learning_objectives': ['sadness_management', 'emotional_expression', 'support_seeking']
            },
            {
                'id': 'anger_regulation',
                'title': '🌈 The Storm Cloud Phoenix',
                'scenario': 'A phoenix got really angry when someone broke their favorite magical crystal. What should the phoenix do with these big feelings?',
                'options': [
                    {'text': 'Count to ten while flapping wings slowly', 'emotion_indicators': ['self_regulation', 'patience'], 'points': 10},
                    {'text': 'Tell someone about the angry feelings', 'emotion_indicators': ['communication', 'emotional_awareness'], 'points': 9},
                    {'text': 'Do some high flying to cool down', 'emotion_indicators': ['physical_coping', 'self_care'], 'points': 8},
                    {'text': 'Think about how to fix or replace the crystal', 'emotion_indicators': ['problem_solving', 'focus'], 'points': 7}
                ],
                'learning_objectives': ['anger_management', 'emotional_regulation', 'coping_skills']
            },
            {
                'id': 'joy_sharing',
                'title': '✨ The Celebration Sprite',
                'scenario': 'A little sprite just learned how to create rainbow sparkles and is bursting with excitement! How should they share their joy?',
                'options': [
                    {'text': 'Teach friends how to make sparkles too', 'emotion_indicators': ['sharing', 'generosity'], 'points': 10},
                    {'text': 'Create a beautiful sparkle show for everyone', 'emotion_indicators': ['performance', 'joy_expression'], 'points': 9},
                    {'text': 'Thank everyone who helped them learn', 'emotion_indicators': ['gratitude', 'appreciation'], 'points': 8},
                    {'text': 'Use sparkles to make others happy', 'emotion_indicators': ['altruism', 'kindness'], 'points': 9}
                ],
                'learning_objectives': ['joy_expression', 'sharing', 'gratitude']
            }
        ]
    
    def load_fantasy_characters(self):
        """Load fantasy characters for emotional storytelling"""
        return [
            {
                'name': 'Luna the Moon Wolf',
                'traits': ['wise', 'calm', 'protective'],
                'special_power': 'Creates peaceful dreams',
                'emotion_specialty': 'helps with anxiety and fear'
            },
            {
                'name': 'Sparkle the Crystal Dragon',
                'traits': ['joyful', 'energetic', 'creative'],
                'special_power': 'Makes rainbow crystals when happy',
                'emotion_specialty': 'helps express and share joy'
            },
            {
                'name': 'Sage the Garden Phoenix',
                'traits': ['patient', 'understanding', 'healing'],
                'special_power': 'Grows healing flowers with song',
                'emotion_specialty': 'helps process sadness and grief'
            },
            {
                'name': 'Thunder the Storm Unicorn',
                'traits': ['strong', 'brave', 'protective'],
                'special_power': 'Controls weather with emotions',
                'emotion_specialty': 'helps manage anger and frustration'
            }
        ]

@emotional_assessment_bp.route('/emotional_assessment')
def start_assessment():
    """Start the emotional assessment game"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in first'}), 401
    
    assessment_game = EmotionalAssessmentGame()
    
    # Select random scenarios based on user's emotional history
    user = User.query.get(session['user_id'])
    selected_scenarios = random.sample(assessment_game.scenarios, min(3, len(assessment_game.scenarios)))
    
    return render_template('assessment/emotional_assessment.html', 
                         scenarios=selected_scenarios,
                         fantasy_characters=assessment_game.fantasy_characters,
                         user=user)

@emotional_assessment_bp.route('/submit_emotional_response', methods=['POST'])
def submit_emotional_response():
    """Process emotional assessment responses with AI analysis"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in first'}), 401
    
    data = request.get_json()
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Process responses with AI
    responses = data.get('responses', [])
    total_score = 0
    emotion_indicators = []
    learning_needs = []
    
    assessment_game = EmotionalAssessmentGame()
    
    for response in responses:
        scenario_id = response.get('scenario_id')
        selected_option = response.get('selected_option')
        
        # Find the scenario and option
        scenario = next((s for s in assessment_game.scenarios if s['id'] == scenario_id), None)
        if scenario and selected_option < len(scenario['options']):
            option = scenario['options'][selected_option]
            total_score += option['points']
            emotion_indicators.extend(option['emotion_indicators'])
            learning_needs.extend(scenario['learning_objectives'])
    
    # AI-powered emotional analysis
    emotional_profile = emotion_ai.analyze_emotional_responses(responses, emotion_indicators)
    
    # Generate personalized learning plan
    learning_plan = realtime_ai.generate_emotional_learning_plan(
        user_emotional_state=emotional_profile,
        identified_needs=learning_needs,
        user_age=user.age,
        user_interests=user.interests
    )
    
    # Create emotion log entry
    emotion_log = EmotionLog(
        user_id=user_id,
        emotion_type='assessment',
        intensity=emotional_profile.get('emotional_intensity', 5),
        context='initial_assessment',
        ai_analysis=json.dumps(emotional_profile),
        learning_recommendations=json.dumps(learning_plan),
        metadata=json.dumps({
            'assessment_score': total_score,
            'emotion_indicators': emotion_indicators,
            'completion_time': data.get('completion_time', 0)
        })
    )
    
    db.session.add(emotion_log)
    
    # Update user's emotional profile
    user.emotional_intelligence_score = total_score
    user.learning_preferences = json.dumps(learning_plan.get('preferences', {}))
    user.support_needs = json.dumps(learning_plan.get('support_areas', []))
    
    db.session.commit()
    
    # Generate personalized feedback with AI
    feedback = emotion_ai.generate_assessment_feedback(
        score=total_score,
        emotional_profile=emotional_profile,
        learning_plan=learning_plan,
        user_name=user.username
    )
    
    return jsonify({
        'success': True,
        'total_score': total_score,
        'emotional_profile': emotional_profile,
        'learning_plan': learning_plan,
        'personalized_feedback': feedback,
        'recommended_activities': learning_plan.get('recommended_activities', []),
        'emotional_support_character': emotion_ai.assign_support_character(emotional_profile),
        'next_steps': learning_plan.get('immediate_actions', [])
    })

@emotional_assessment_bp.route('/emotion_story_response', methods=['POST'])
def process_emotion_story():
    """Process user's response to emotional story scenarios"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in first'}), 401
    
    data = request.get_json()
    user_id = session['user_id']
    
    story_response = data.get('story_response', '')
    emotion_context = data.get('emotion_context', '')
    
    # AI analysis of story response
    story_analysis = emotion_ai.analyze_story_emotional_content(
        story_response, 
        emotion_context
    )
    
    # Real-time learning from user's creative expression
    learning_insights = realtime_ai.learn_from_user_creativity(
        user_id=user_id,
        creative_content=story_response,
        emotional_context=emotion_context,
        analysis_results=story_analysis
    )
    
    # Log the emotional story interaction
    emotion_log = EmotionLog(
        user_id=user_id,
        emotion_type='creative_expression',
        intensity=story_analysis.get('emotional_intensity', 5),
        context='story_creation',
        ai_analysis=json.dumps(story_analysis),
        learning_recommendations=json.dumps(learning_insights),
        metadata=json.dumps({
            'story_length': len(story_response),
            'creativity_score': story_analysis.get('creativity_score', 0),
            'emotional_depth': story_analysis.get('emotional_depth', 0)
        })
    )
    
    db.session.add(emotion_log)
    db.session.commit()
    
    # Generate encouraging feedback
    feedback = emotion_ai.generate_creative_feedback(
        story_response,
        story_analysis,
        learning_insights
    )
    
    return jsonify({
        'success': True,
        'analysis': story_analysis,
        'feedback': feedback,
        'learning_insights': learning_insights,
        'emotional_growth_points': story_analysis.get('growth_points', 0),
        'creativity_badge': story_analysis.get('creativity_level', 'emerging_artist')
    })

@emotional_assessment_bp.route('/daily_mood_check', methods=['POST'])
def daily_mood_check():
    """Daily mood check-in with AI-powered recommendations"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in first'}), 401
    
    data = request.get_json()
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    mood_data = {
        'mood_level': data.get('mood_level', 5),  # 1-10 scale
        'mood_type': data.get('mood_type', 'neutral'),
        'energy_level': data.get('energy_level', 5),
        'social_feeling': data.get('social_feeling', 'neutral'),
        'learning_motivation': data.get('learning_motivation', 5),
        'stress_level': data.get('stress_level', 3),
        'notes': data.get('notes', '')
    }
    
    # AI analysis of daily mood
    mood_analysis = emotion_ai.analyze_daily_mood(mood_data, user_id)
    
    # Generate personalized daily recommendations
    daily_recommendations = realtime_ai.generate_daily_recommendations(
        mood_analysis=mood_analysis,
        user_preferences=user.learning_preferences,
        historical_data=emotion_ai.get_user_mood_history(user_id)
    )
    
    # Log daily mood
    emotion_log = EmotionLog(
        user_id=user_id,
        emotion_type='daily_checkin',
        intensity=mood_data['mood_level'],
        context='daily_mood',
        ai_analysis=json.dumps(mood_analysis),
        learning_recommendations=json.dumps(daily_recommendations),
        metadata=json.dumps(mood_data)
    )
    
    db.session.add(emotion_log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'mood_analysis': mood_analysis,
        'daily_recommendations': daily_recommendations,
        'supportive_message': emotion_ai.generate_supportive_message(mood_analysis),
        'recommended_pet_activity': daily_recommendations.get('pet_activity'),
        'learning_suggestion': daily_recommendations.get('learning_activity'),
        'wellness_tip': daily_recommendations.get('wellness_tip')
    })

@emotional_assessment_bp.route('/emotion_pattern_analysis')
def get_emotion_patterns():
    """Get AI analysis of user's emotional patterns over time"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in first'}), 401
    
    user_id = session['user_id']
    
    # Get historical emotion data
    emotion_history = EmotionLog.query.filter_by(
        user_id=user_id
    ).order_by(EmotionLog.created_at.desc()).limit(30).all()
    
    # AI pattern analysis
    pattern_analysis = emotion_ai.analyze_emotional_patterns(emotion_history)
    
    # Generate insights and recommendations
    insights = realtime_ai.generate_pattern_insights(
        pattern_analysis,
        user_id
    )
    
    return jsonify({
        'success': True,
        'pattern_analysis': pattern_analysis,
        'insights': insights,
        'growth_areas': pattern_analysis.get('growth_opportunities', []),
        'strengths': pattern_analysis.get('emotional_strengths', []),
        'recommendations': insights.get('personalized_recommendations', []),
        'next_learning_goals': insights.get('suggested_goals', [])
    })