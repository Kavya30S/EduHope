from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.models.emotion import EmotionData
from app.models.user import User
from app.models.pet import Pet
from app.services.sentiment_service import SentimentService
from app.services.llm_service import LLMService
from app.database import db
import json
from datetime import datetime, timedelta
import random

support_bp = Blueprint('support', __name__)
sentiment_service = SentimentService()
llm_service = LLMService()

@support_bp.route('/emotion-check')
@login_required
def emotion_check():
    """Daily emotion check-in interface"""
    recent_emotions = EmotionData.query.filter_by(
        user_id=current_user.id
    ).order_by(EmotionData.timestamp.desc()).limit(7).all()
    
    return render_template('emotion_check.html', 
                         recent_emotions=recent_emotions)

@support_bp.route('/record-emotion', methods=['POST'])
@login_required
def record_emotion():
    """Record user's emotional state"""
    data = request.get_json()
    
    emotion_entry = EmotionData(
        user_id=current_user.id,
        emotion_type=data.get('emotion'),
        intensity=data.get('intensity', 5),
        context=data.get('context', ''),
        trigger=data.get('trigger', ''),
        timestamp=datetime.utcnow()
    )
    
    # Analyze emotion context if provided
    if emotion_entry.context:
        sentiment = sentiment_service.analyze_sentiment(emotion_entry.context)
        emotion_entry.sentiment_score = sentiment.get('score', 0)
        emotion_entry.sentiment_label = sentiment.get('label', 'neutral')
    
    db.session.add(emotion_entry)
    db.session.commit()
    
    # Get personalized response and coping strategies
    response = generate_emotional_response(emotion_entry)
    
    # Update pet based on emotional state
    update_pet_emotional_response(current_user, emotion_entry)
    
    return jsonify({
        'success': True,
        'response': response,
        'coping_strategies': get_coping_strategies(emotion_entry),
        'pet_support': get_pet_emotional_support(emotion_entry)
    })

@support_bp.route('/mood-tracker')
@login_required
def mood_tracker():
    """Comprehensive mood tracking dashboard"""
    # Get mood data for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    mood_data = EmotionData.query.filter(
        EmotionData.user_id == current_user.id,
        EmotionData.timestamp >= thirty_days_ago
    ).order_by(EmotionData.timestamp).all()
    
    # Analyze patterns
    mood_patterns = analyze_mood_patterns(mood_data)
    
    return render_template('mood_tracker.html',
                         mood_data=mood_data,
                         patterns=mood_patterns)

@support_bp.route('/breathing-exercise')
@login_required
def breathing_exercise():
    """Guided breathing exercise for stress relief"""
    return render_template('breathing_exercise.html')

@support_bp.route('/mindfulness-activity')
@login_required
def mindfulness_activity():
    """Interactive mindfulness activities"""
    activities = [
        {
            'name': 'Rainbow Observation',
            'description': 'Find 7 different colors around you',
            'duration': 5,
            'type': 'visual'
        },
        {
            'name': 'Gratitude Garden',
            'description': 'Think of 3 things you\'re grateful for',
            'duration': 3,
            'type': 'reflection'
        },
        {
            'name': 'Body Scan Adventure',
            'description': 'Travel through your body with awareness',
            'duration': 10,
            'type': 'physical'
        },
        {
            'name': 'Sound Safari',
            'description': 'Listen for 5 different sounds',
            'duration': 3,
            'type': 'auditory'
        }
    ]
    
    return render_template('mindfulness_activity.html', activities=activities)

@support_bp.route('/virtual-counselor', methods=['GET', 'POST'])
@login_required
def virtual_counselor():
    """AI-powered virtual counselor chat"""
    if request.method == 'POST':
        data = request.get_json()
        message = data.get('message', '')
        
        # Analyze message for emotional content
        emotion_analysis = sentiment_service.analyze_detailed_emotion(message)
        
        # Generate appropriate counselor response
        counselor_response = generate_counselor_response(message, emotion_analysis)
        
        # Store conversation for continuity
        store_counselor_conversation(current_user.id, message, counselor_response)
        
        # Check if crisis intervention is needed
        crisis_check = check_crisis_indicators(message, emotion_analysis)
        
        return jsonify({
            'response': counselor_response,
            'emotion_detected': emotion_analysis,
            'crisis_support': crisis_check,
            'suggested_activities': get_suggested_activities(emotion_analysis)
        })
    
    # Get conversation history
    conversation_history = get_counselor_history(current_user.id)
    
    return render_template('virtual_counselor.html',
                         conversation_history=conversation_history)

@support_bp.route('/stress-relief-games')
@login_required
def stress_relief_games():
    """Stress relief games and activities"""
    games = [
        {
            'name': 'Bubble Pop Zen',
            'description': 'Pop colorful bubbles to release stress',
            'category': 'interactive',
            'duration': '5-10 minutes'
        },
        {
            'name': 'Digital Sandbox',
            'description': 'Create patterns in virtual sand',
            'category': 'creative',
            'duration': '10-15 minutes'
        },
        {
            'name': 'Calming Coloring',
            'description': 'Color beautiful mandala patterns',
            'category': 'artistic',
            'duration': '15-20 minutes'
        },
        {
            'name': 'Nature Sounds Journey',
            'description': 'Relax with ambient nature sounds',
            'category': 'audio',
            'duration': '10-30 minutes'
        }
    ]
    
    return render_template('stress_relief_games.html', games=games)

@support_bp.route('/emotional-journal')
@login_required
def emotional_journal():
    """Personal emotional journaling interface"""
    journal_entries = get_journal_entries(current_user.id)
    writing_prompts = get_emotional_writing_prompts()
    
    return render_template('emotional_journal.html',
                         entries=journal_entries,
                         prompts=writing_prompts)

@support_bp.route('/save-journal-entry', methods=['POST'])
@login_required
def save_journal_entry():
    """Save journal entry with emotional analysis"""
    data = request.get_json()
    entry_text = data.get('entry', '')
    
    # Analyze emotional content
    emotion_analysis = sentiment_service.analyze_detailed_emotion(entry_text)
    
    # Save journal entry
    journal_entry = {
        'user_id': current_user.id,
        'content': entry_text,
        'emotions_detected': emotion_analysis,
        'timestamp': datetime.utcnow().isoformat(),
        'word_count': len(entry_text.split())
    }
    
    save_journal_entry_to_db(journal_entry)
    
    # Generate supportive feedback
    feedback = generate_journal_feedback(entry_text, emotion_analysis)
    
    return jsonify({
        'success': True,
        'feedback': feedback,
        'emotions_detected': emotion_analysis,
        'encouragement': get_writing_encouragement()
    })

@support_bp.route('/emotional-support-pet')
@login_required
def emotional_support_pet():
    """Emotional support interactions with pet"""
    user_pet = Pet.query.filter_by(user_id=current_user.id).first()
    recent_emotions = get_recent_emotional_state(current_user.id)
    
    pet_activities = generate_emotional_pet_activities(user_pet, recent_emotions)
    
    return render_template('emotional_support_pet.html',
                         pet=user_pet,
                         activities=pet_activities,
                         recent_emotions=recent_emotions)

@support_bp.route('/crisis-support')
@login_required
def crisis_support():
    """Crisis support resources and immediate help"""
    support_resources = {
        'immediate_help': [
            {
                'name': 'Crisis Text Line',
                'contact': 'Text HOME to 741741',
                'description': '24/7 crisis support via text'
            },
            {
                'name': 'National Suicide Prevention Lifeline',
                'contact': '988',
                'description': '24/7 phone support'
            }
        ],
        'coping_strategies': [
            'Deep breathing exercises',
            'Talk to your virtual pet',
            'Write in your journal',
            'Use the mindfulness activities'
        ]
    }
    
    return render_template('crisis_support.html', resources=support_resources)

# Helper functions for emotional support

def generate_emotional_response(emotion_entry):
    """Generate personalized response to emotional state"""
    emotion_responses = {
        'happy': [
            "I'm so glad you're feeling happy! Your joy is wonderful to see! 🌟",
            "Happiness looks great on you! What made your day special? ✨",
            "Your happiness is contagious! Keep spreading those good vibes! 😊"
        ],
        'sad': [
            "I see you're feeling sad right now. It's okay to feel this way. 💙",
            "Sadness is a natural emotion. I'm here to support you through this. 🤗",
            "Your feelings are valid. Would you like to talk about what's making you sad? 💛"
        ],
        'angry': [
            "I understand you're feeling angry. Let's find healthy ways to express this. 🔥➡️💨",
            "Anger can be overwhelming. Take some deep breaths with me. 🌬️",
            "It's okay to feel angry. Let's work through this together. 💪"
        ],
        'anxious': [
            "I can see you're feeling anxious. You're safe here with me. 🛡️",
            "Anxiety can be tough. Let's try some calming techniques together. 🌊",
            "Your anxious feelings are understandable. I'm here to help you feel better. 🕊️"
        ],
        'excited': [
            "Your excitement is amazing! Tell me more about what's got you so thrilled! 🎉",
            "I love seeing you excited! Your energy is infectious! ⚡",
            "Excitement is such a wonderful feeling! Share your joy with me! 🌈"
        ]
    }
    
    emotion = emotion_entry.emotion_type.lower()
    responses = emotion_responses.get(emotion, [
        "Thank you for sharing your feelings with me. I'm here to support you. 💕"
    ])
    
    return random.choice(responses)

def get_coping_strategies(emotion_entry):
    """Get personalized coping strategies based on emotion"""
    strategies = {
        'sad': [
            "Talk to your pet companion - they're great listeners!",
            "Write in your emotional journal about your feelings",
            "Try the 'Gratitude Garden' mindfulness activity",
            "Listen to some calming nature sounds"
        ],
        'angry': [
            "Take 10 deep breaths with the breathing exercise",
            "Try the 'Bubble Pop Zen' game to release tension",
            "Write about your anger in your journal",
            "Do some physical movement with your pet"
        ],
        'anxious': [
            "Use the guided breathing exercise",
            "Try the 'Body Scan Adventure' mindfulness activity",
            "Spend calming time with your pet companion",
            "Practice the 'Rainbow Observation' grounding technique"
        ],
        'excited': [
            "Channel your energy into learning something new!",
            "Share your excitement by teaching your pet new tricks",
            "Write about what's making you excited in your journal",
            "Use your energy for creative activities"
        ],
        'lonely': [
            "Spend quality time with your virtual pet",
            "Write a letter to yourself in your journal",
            "Try the collaborative storytelling feature",
            "Remember: you're never truly alone - I'm here with you"
        ]
    }
    
    emotion = emotion_entry.emotion_type.lower()
    return strategies.get(emotion, [
        "Take some time for self-care",
        "Practice mindfulness",
        "Connect with your pet companion",
        "Remember that all feelings are temporary"
    ])

def update_pet_emotional_response(user, emotion_entry):
    """Update pet's response based on user's emotional state"""
    pet = Pet.query.filter_by(user_id=user.id).first()
    if not pet:
        return
    
    # Adjust pet's emotional state based on user's emotion
    emotion = emotion_entry.emotion_type.lower()
    
    if emotion in ['sad', 'angry', 'anxious']:
        # Pet becomes more caring and attentive
        pet.happiness = max(pet.happiness - 10, 0)  # Pet is concerned
        pet.care_giving_mode = True
        pet.last_emotional_support = datetime.utcnow()
    elif emotion in ['happy', 'excited']:
        # Pet becomes happier too
        pet.happiness = min(pet.happiness + 15, 100)
        pet.energy = min(pet.energy + 10, 100)
    
    # Update pet's emotional intelligence
    pet.emotional_bond = min(pet.emotional_bond + 1, 100)
    
    db.session.commit()

def get_pet_emotional_support(emotion_entry):
    """Get pet's emotional support response"""
    emotion = emotion_entry.emotion_type.lower()
    
    pet_responses = {
        'sad': {
            'message': "Your pet nuzzles up to you with gentle, caring eyes 🐾💙",
            'action': "comfort_cuddle",
            'sound': "gentle_purr"
        },
        'angry': {
            'message': "Your pet sits calmly beside you, offering peaceful energy 🐾🕊️",
            'action': "calming_presence",
            'sound': "soft_breathing"
        },
        'anxious': {
            'message': "Your pet does slow, rhythmic movements to help you breathe 🐾🌬️",
            'action': "breathing_guide",
            'sound': "steady_heartbeat"
        },
        'happy': {
            'message': "Your pet bounces with joy, celebrating your happiness! 🐾🎉",
            'action': "happy_dance",
            'sound': "joyful_chirp"
        },
        'excited': {
            'message': "Your pet's eyes sparkle with shared excitement! 🐾✨",
            'action': "excited_spin",
            'sound': "enthusiastic_bark"
        }
    }
    
    return pet_responses.get(emotion, {
        'message': "Your pet stays close by, offering unconditional love 🐾💕",
        'action': "supportive_presence",
        'sound': "gentle_hum"
    })

def analyze_mood_patterns(mood_data):
    """Analyze mood patterns for insights"""
    if not mood_data:
        return {}
    
    patterns = {
        'most_common_emotion': get_most_common_emotion(mood_data),
        'emotion_frequency': get_emotion_frequency(mood_data),
        'intensity_trends': get_intensity_trends(mood_data),
        'time_patterns': get_time_patterns(mood_data),
        'improvement_areas': get_improvement_suggestions(mood_data)
    }
    
    return patterns

def generate_counselor_response(message, emotion_analysis):
    """Generate appropriate counselor response"""
    # Use LLM service to generate empathetic response
    context = {
        'user_emotion': emotion_analysis.get('primary_emotion', 'neutral'),
        'intensity': emotion_analysis.get('intensity', 0.5),
        'previous_context': get_recent_counselor_context(current_user.id)
    }
    
    response = llm_service.generate_counselor_response(message, context)
    
    # Add emotional validation
    validation_phrases = [
        "Your feelings are completely valid.",
        "It takes courage to share these thoughts.",
        "I'm here to listen and support you.",
        "You're not alone in feeling this way."
    ]
    
    if emotion_analysis.get('intensity', 0) > 0.7:
        response += f" {random.choice(validation_phrases)}"
    
    return response

def check_crisis_indicators(message, emotion_analysis):
    """Check for crisis indicators and provide appropriate support"""
    crisis_keywords = [
        'hurt myself', 'end it all', 'can\'t go on', 'give up',
        'worthless', 'hopeless', 'suicide', 'kill myself'
    ]
    
    message_lower = message.lower()
    crisis_detected = any(keyword in message_lower for keyword in crisis_keywords)
    
    if crisis_detected or emotion_analysis.get('intensity', 0) > 0.9:
        return {
            'crisis_detected': True,
            'immediate_resources': [
                {
                    'name': 'Crisis Text Line',
                    'contact': 'Text HOME to 741741',
                    'available': '24/7'
                },
                {
                    'name': 'National Suicide Prevention Lifeline',
                    'contact': '988',
                    'available': '24/7'
                }
            ],
            'message': "I'm concerned about you. Please reach out to these crisis resources immediately. You matter, and help is available."
        }
    
    return {'crisis_detected': False}

def get_suggested_activities(emotion_analysis):
    """Get activity suggestions based on emotional state"""
    primary_emotion = emotion_analysis.get('primary_emotion', 'neutral')
    intensity = emotion_analysis.get('intensity', 0.5)
    
    activities = {
        'sad': [
            {'name': 'Pet Cuddle Time', 'duration': '10 minutes', 'type': 'comfort'},
            {'name': 'Gratitude Journal', 'duration': '15 minutes', 'type': 'reflection'},
            {'name': 'Gentle Nature Sounds', 'duration': '20 minutes', 'type': 'relaxation'}
        ],
        'anxious': [
            {'name': 'Breathing Exercise', 'duration': '5 minutes', 'type': 'calming'},
            {'name': 'Progressive Muscle Relaxation', 'duration': '15 minutes', 'type': 'physical'},
            {'name': 'Mindful Coloring', 'duration': '20 minutes', 'type': 'creative'}
        ],
        'angry': [
            {'name': 'Bubble Pop Game', 'duration': '5 minutes', 'type': 'release'},
            {'name': 'Physical Exercise with Pet', 'duration': '15 minutes', 'type': 'movement'},
            {'name': 'Anger Journal Writing', 'duration': '10 minutes', 'type': 'expression'}
        ]
    }
    
    return activities.get(primary_emotion, [
        {'name': 'Check in with Pet', 'duration': '5 minutes', 'type': 'connection'},
        {'name': 'Quick Mindfulness', 'duration': '3 minutes', 'type': 'awareness'}
    ])

def get_emotional_writing_prompts():
    """Get writing prompts for emotional journaling"""
    prompts = [
        "Today I felt... because...",
        "Three things I'm grateful for right now are...",
        "When I feel overwhelmed, what helps me most is...",
        "A person who makes me feel supported is... because...",
        "My favorite way to show myself kindness is...",
        "When I'm feeling strong, I like to...",
        "Something beautiful I noticed today was...",
        "A challenge I overcame recently was...",
        "My pet makes me feel... when...",
        "If I could tell my younger self one thing, it would be..."
    ]
    
    return random.sample(prompts, 3)

def generate_journal_feedback(entry_text, emotion_analysis):
    """Generate supportive feedback for journal entries"""
    word_count = len(entry_text.split())
    primary_emotion = emotion_analysis.get('primary_emotion', 'neutral')
    
    feedback_templates = {
        'sad': [
            f"Thank you for sharing your feelings. Writing {word_count} words shows your courage in expressing difficult emotions.",
            "Your honesty in this entry is powerful. Remember that sad feelings are temporary, and you're taking positive steps by journaling."
        ],
        'happy': [
            f"Your joy shines through these {word_count} words! It's wonderful to document happy moments.",
            "Reading about your happiness made me smile too! These positive memories are treasures to look back on."
        ],
        'anxious': [
            f"Writing down anxious thoughts can be very helpful. Your {word_count} words show you're processing these feelings constructively.",
            "Thank you for trusting your journal with these worries. Getting them out of your head and onto paper is a brave step."
        ]
    }
    
    templates = feedback_templates.get(primary_emotion, [
        f"Your {word_count} words of reflection show real self-awareness. Keep exploring your thoughts and feelings.",
        "Thank you for taking time to write. Self-reflection through journaling is a gift you give yourself."
    ])
    
    return random.choice(templates)

def generate_emotional_pet_activities(pet, recent_emotions):
    """Generate pet activities based on emotional state"""
    if not recent_emotions:
        return standard_pet_activities()
    
    primary_emotion = get_dominant_recent_emotion(recent_emotions)
    
    activities = {
        'sad': [
            {
                'name': 'Comfort Cuddles',
                'description': 'Your pet offers gentle, healing cuddles',
                'duration': '10 minutes',
                'benefit': 'Releases oxytocin, reduces stress'
            },
            {
                'name': 'Peaceful Garden Walk',
                'description': 'Take a slow, mindful walk with your pet in a virtual garden',
                'duration': '15 minutes',
                'benefit': 'Promotes calm and connection with nature'
            }
        ],
        'anxious': [
            {
                'name': 'Synchronized Breathing',
                'description': 'Breathe in rhythm with your pet\'s gentle movements',
                'duration': '5 minutes',
                'benefit': 'Activates parasympathetic nervous system'
            },
            {
                'name': 'Grounding Touch',
                'description': 'Feel your pet\'s warmth and steady presence',
                'duration': '8 minutes',
                'benefit': 'Provides grounding and reduces anxiety'
            }
        ],
        'happy': [
            {
                'name': 'Celebration Dance',
                'description': 'Dance and play with your happy pet!',
                'duration': '10 minutes',
                'benefit': 'Amplifies joy and creates positive memories'
            },
            {
                'name': 'Adventure Planning',
                'description': 'Plan exciting virtual adventures with your pet',
                'duration': '20 minutes',
                'benefit': 'Builds anticipation and excitement'
            }
        ]
    }
    
    return activities.get(primary_emotion, standard_pet_activities())

def standard_pet_activities():
    """Standard pet activities for neutral emotional states"""
    return [
        {
            'name': 'Daily Check-in',
            'description': 'See how your pet is feeling today',
            'duration': '5 minutes',
            'benefit': 'Builds routine and connection'
        },
        {
            'name': 'Learning Together',
            'description': 'Teach your pet something new',
            'duration': '15 minutes',
            'benefit': 'Enhances bond and cognitive engagement'
        }
    ]

# Database helper functions
def save_journal_entry_to_db(journal_entry):
    """Save journal entry to database"""
    # This would typically save to a JournalEntry model
    # For now, we'll store in user's session or a simple format
    if 'journal_entries' not in session:
        session['journal_entries'] = []
    
    session['journal_entries'].append(journal_entry)
    session['journal_entries'] = session['journal_entries'][-50:]  # Keep last 50

def store_counselor_conversation(user_id, message, response):
    """Store counselor conversation for continuity"""
    if 'counselor_history' not in session:
        session['counselor_history'] = []
    
    conversation = {
        'user_message': message,
        'counselor_response': response,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    session['counselor_history'].append(conversation)
    session['counselor_history'] = session['counselor_history'][-20:]  # Keep last 20

def get_recent_emotional_state(user_id):
    """Get user's recent emotional state"""
    recent_date = datetime.utcnow() - timedelta(days=3)
    return EmotionData.query.filter(
        EmotionData.user_id == user_id,
        EmotionData.timestamp >= recent_date
    ).order_by(EmotionData.timestamp.desc()).limit(10).all()

def get_writing_encouragement():
    """Get encouraging message for writing"""
    encouragements = [
        "Your words have power. Keep writing! ✍️",
        "Every word you write is a step toward understanding yourself better.",
        "Writing is a form of self-care. Thank you for taking care of yourself.",
        "Your thoughts and feelings matter. Thank you for sharing them.",
        "Keep exploring your inner world through writing. You're doing great!"
    ]
    
    return random.choice(encouragements)