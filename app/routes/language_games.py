from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.models.user import User
from app.models.lesson import Lesson
from app.models.achievement import Achievement
from app.models.pet import Pet
from app.services.voice_service import VoiceService
from app.services.translation_service import TranslationService
from app.services.llm_service import LLMService
from app import db
import random
import json
from datetime import datetime
import logging

language_games_bp = Blueprint('language_games', __name__)
voice_service = VoiceService()
translation_service = TranslationService()
llm_service = LLMService()

# Enhanced vocabulary database with child-friendly words
VOCABULARY_SETS = {
    'beginner': {
        'animals': ['cat', 'dog', 'bird', 'fish', 'rabbit', 'elephant', 'lion', 'bear', 'monkey', 'tiger'],
        'colors': ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'black', 'white', 'brown'],
        'numbers': ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'],
        'family': ['mother', 'father', 'sister', 'brother', 'baby', 'grandma', 'grandpa', 'uncle', 'aunt', 'friend'],
        'food': ['apple', 'banana', 'bread', 'milk', 'cake', 'cookie', 'pizza', 'ice cream', 'juice', 'candy']
    },
    'intermediate': {
        'emotions': ['happy', 'sad', 'angry', 'excited', 'scared', 'surprised', 'proud', 'worried', 'calm', 'brave'],
        'actions': ['run', 'jump', 'dance', 'sing', 'draw', 'read', 'write', 'play', 'laugh', 'cry'],
        'nature': ['tree', 'flower', 'sun', 'moon', 'star', 'rain', 'snow', 'wind', 'ocean', 'mountain'],
        'school': ['book', 'pencil', 'teacher', 'student', 'classroom', 'homework', 'test', 'friend', 'learn', 'study'],
        'body': ['head', 'eyes', 'nose', 'mouth', 'ears', 'hands', 'feet', 'hair', 'teeth', 'heart']
    },
    'advanced': {
        'adventures': ['journey', 'treasure', 'mystery', 'castle', 'forest', 'dragon', 'princess', 'knight', 'magic', 'quest'],
        'science': ['planet', 'rocket', 'experiment', 'discovery', 'invention', 'robot', 'computer', 'energy', 'space', 'future'],
        'feelings': ['confident', 'generous', 'curious', 'patient', 'creative', 'determined', 'peaceful', 'grateful', 'hopeful', 'courageous'],
        'community': ['neighbor', 'helper', 'doctor', 'teacher', 'firefighter', 'police', 'farmer', 'cook', 'artist', 'musician']
    }
}

@language_games_bp.route('/language_games')
@login_required
def language_games():
    """Main language games dashboard"""
    user_level = get_user_language_level(current_user.id)
    available_games = get_available_games(user_level)
    user_stats = get_user_language_stats(current_user.id)
    
    return render_template('language_game.html', 
                         games=available_games, 
                         user_level=user_level,
                         stats=user_stats)

@language_games_bp.route('/vocabulary_match')
@login_required
def vocabulary_match():
    """Vocabulary matching game with images"""
    level = request.args.get('level', 'beginner')
    category = request.args.get('category', 'animals')
    
    words = VOCABULARY_SETS.get(level, {}).get(category, [])
    if not words:
        return jsonify({'error': 'Invalid level or category'}), 400
    
    # Select random words for the game
    game_words = random.sample(words, min(6, len(words)))
    
    # Generate distractors using LLM
    distractors = llm_service.generate_vocabulary_distractors(game_words, category)
    
    game_data = {
        'words': game_words,
        'distractors': distractors,
        'category': category,
        'level': level,
        'time_limit': 60
    }
    
    return jsonify(game_data)

@language_games_bp.route('/pronunciation_challenge')
@login_required
def pronunciation_challenge():
    """Speech recognition pronunciation game"""
    level = request.args.get('level', 'beginner')
    category = request.args.get('category', 'animals')
    
    words = VOCABULARY_SETS.get(level, {}).get(category, [])
    if not words:
        return jsonify({'error': 'Invalid level or category'}), 400
    
    # Select words for pronunciation
    challenge_words = random.sample(words, min(5, len(words)))
    
    # Get pronunciation tips using LLM
    pronunciation_tips = {}
    for word in challenge_words:
        tips = llm_service.generate_pronunciation_tips(word)
        pronunciation_tips[word] = tips
    
    game_data = {
        'words': challenge_words,
        'pronunciation_tips': pronunciation_tips,
        'level': level,
        'category': category
    }
    
    return jsonify(game_data)

@language_games_bp.route('/submit_pronunciation', methods=['POST'])
@login_required
def submit_pronunciation():
    """Process pronunciation submission"""
    try:
        audio_data = request.files.get('audio')
        target_word = request.form.get('word')
        
        if not audio_data or not target_word:
            return jsonify({'error': 'Missing audio or target word'}), 400
        
        # Process speech recognition
        recognized_text = voice_service.speech_to_text(audio_data)
        
        # Calculate pronunciation accuracy
        accuracy = calculate_pronunciation_accuracy(recognized_text, target_word)
        
        # Update user progress
        update_language_progress(current_user.id, 'pronunciation', accuracy)
        
        # Reward system
        reward = calculate_pronunciation_reward(accuracy)
        update_user_rewards(current_user.id, reward)
        
        # Update pet happiness based on performance
        update_pet_from_learning(current_user.id, accuracy)
        
        return jsonify({
            'recognized': recognized_text,
            'accuracy': accuracy,
            'reward': reward,
            'feedback': get_pronunciation_feedback(accuracy)
        })
        
    except Exception as e:
        logging.error(f"Pronunciation submission error: {str(e)}")
        return jsonify({'error': 'Processing failed'}), 500

@language_games_bp.route('/story_builder')
@login_required
def story_builder():
    """Interactive story building game"""
    level = request.args.get('level', 'beginner')
    theme = request.args.get('theme', 'adventure')
    
    # Generate story prompts using LLM
    story_prompts = llm_service.generate_story_prompts(level, theme)
    
    # Get vocabulary suggestions
    vocab_suggestions = get_story_vocabulary(level, theme)
    
    game_data = {
        'prompts': story_prompts,
        'vocabulary': vocab_suggestions,
        'level': level,
        'theme': theme,
        'min_words': get_min_words_for_level(level)
    }
    
    return jsonify(game_data)

@language_games_bp.route('/submit_story', methods=['POST'])
@login_required
def submit_story():
    """Submit and evaluate user story"""
    try:
        story_text = request.json.get('story')
        level = request.json.get('level')
        theme = request.json.get('theme')
        
        if not story_text:
            return jsonify({'error': 'No story provided'}), 400
        
        # Analyze story using LLM
        analysis = llm_service.analyze_user_story(story_text, level, theme)
        
        # Calculate scores
        creativity_score = analysis.get('creativity', 0)
        vocabulary_score = analysis.get('vocabulary', 0)
        grammar_score = analysis.get('grammar', 0)
        
        overall_score = (creativity_score + vocabulary_score + grammar_score) / 3
        
        # Update user progress
        update_language_progress(current_user.id, 'storytelling', overall_score)
        
        # Generate personalized feedback
        feedback = llm_service.generate_story_feedback(story_text, analysis)
        
        # Reward system
        reward = calculate_story_reward(overall_score, len(story_text))
        update_user_rewards(current_user.id, reward)
        
        # Update pet happiness
        update_pet_from_learning(current_user.id, overall_score)
        
        return jsonify({
            'scores': {
                'creativity': creativity_score,
                'vocabulary': vocabulary_score,
                'grammar': grammar_score,
                'overall': overall_score
            },
            'feedback': feedback,
            'reward': reward,
            'achievements': check_story_achievements(current_user.id, story_text)
        })
        
    except Exception as e:
        logging.error(f"Story submission error: {str(e)}")
        return jsonify({'error': 'Processing failed'}), 500

@language_games_bp.route('/word_puzzle')
@login_required
def word_puzzle():
    """Word puzzle and scramble game"""
    level = request.args.get('level', 'beginner')
    category = request.args.get('category', 'animals')
    
    words = VOCABULARY_SETS.get(level, {}).get(category, [])
    if not words:
        return jsonify({'error': 'Invalid level or category'}), 400
    
    # Create word puzzles
    puzzle_words = random.sample(words, min(5, len(words)))
    puzzles = []
    
    for word in puzzle_words:
        # Create scrambled version
        scrambled = scramble_word(word)
        
        # Generate hints using LLM
        hint = llm_service.generate_word_hint(word, category)
        
        puzzles.append({
            'word': word,
            'scrambled': scrambled,
            'hint': hint,
            'length': len(word)
        })
    
    game_data = {
        'puzzles': puzzles,
        'level': level,
        'category': category,
        'time_limit': 120
    }
    
    return jsonify(game_data)

@language_games_bp.route('/submit_puzzle', methods=['POST'])
@login_required
def submit_puzzle():
    """Submit puzzle solution"""
    try:
        user_answers = request.json.get('answers', [])
        correct_answers = request.json.get('correct_answers', [])
        
        if not user_answers or not correct_answers:
            return jsonify({'error': 'Missing answers'}), 400
        
        # Calculate accuracy
        correct_count = sum(1 for user, correct in zip(user_answers, correct_answers) 
                          if user.lower().strip() == correct.lower().strip())
        accuracy = (correct_count / len(correct_answers)) * 100
        
        # Update progress
        update_language_progress(current_user.id, 'puzzle', accuracy)
        
        # Reward system
        reward = calculate_puzzle_reward(accuracy, len(correct_answers))
        update_user_rewards(current_user.id, reward)
        
        # Update pet
        update_pet_from_learning(current_user.id, accuracy)
        
        return jsonify({
            'correct_count': correct_count,
            'total_count': len(correct_answers),
            'accuracy': accuracy,
            'reward': reward,
            'feedback': get_puzzle_feedback(accuracy)
        })
        
    except Exception as e:
        logging.error(f"Puzzle submission error: {str(e)}")
        return jsonify({'error': 'Processing failed'}), 500

@language_games_bp.route('/translation_game')
@login_required
def translation_game():
    """Translation challenge game"""
    source_lang = request.args.get('source', 'en')
    target_lang = request.args.get('target', 'es')
    level = request.args.get('level', 'beginner')
    
    # Get phrases for translation
    phrases = get_translation_phrases(level, source_lang)
    
    # Translate to target language
    translated_phrases = []
    for phrase in phrases:
        translation = translation_service.translate(phrase, source_lang, target_lang)
        translated_phrases.append({
            'source': phrase,
            'target': translation,
            'difficulty': get_phrase_difficulty(phrase)
        })
    
    game_data = {
        'phrases': translated_phrases,
        'source_lang': source_lang,
        'target_lang': target_lang,
        'level': level
    }
    
    return jsonify(game_data)

# Helper functions
def get_user_language_level(user_id):
    """Determine user's language level based on performance"""
    user = User.query.get(user_id)
    if not user:
        return 'beginner'
    
    # Calculate level based on language_tokens and performance
    tokens = user.language_tokens or 0
    if tokens < 100:
        return 'beginner'
    elif tokens < 500:
        return 'intermediate'
    else:
        return 'advanced'

def get_available_games(level):
    """Get available games for user level"""
    base_games = [
        {'id': 'vocabulary_match', 'name': 'Word Matching', 'icon': '🎯'},
        {'id': 'pronunciation_challenge', 'name': 'Speak & Learn', 'icon': '🎤'},
        {'id': 'word_puzzle', 'name': 'Word Puzzles', 'icon': '🧩'}
    ]
    
    if level in ['intermediate', 'advanced']:
        base_games.extend([
            {'id': 'story_builder', 'name': 'Story Creator', 'icon': '📖'},
            {'id': 'translation_game', 'name': 'Language Bridge', 'icon': '🌍'}
        ])
    
    return base_games

def get_user_language_stats(user_id):
    """Get user's language learning statistics"""
    user = User.query.get(user_id)
    if not user:
        return {}
    
    return {
        'tokens': user.language_tokens or 0,
        'level': get_user_language_level(user_id),
        'games_played': user.games_played or 0,
        'accuracy': user.language_accuracy or 0,
        'streak': user.learning_streak or 0
    }

def calculate_pronunciation_accuracy(recognized, target):
    """Calculate pronunciation accuracy using fuzzy matching"""
    if not recognized or not target:
        return 0
    
    # Simple similarity calculation
    recognized = recognized.lower().strip()
    target = target.lower().strip()
    
    if recognized == target:
        return 100
    
    # Calculate Levenshtein distance
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    distance = levenshtein_distance(recognized, target)
    max_length = max(len(recognized), len(target))
    similarity = (max_length - distance) / max_length
    
    return max(0, min(100, similarity * 100))

def update_language_progress(user_id, game_type, score):
    """Update user's language learning progress"""
    user = User.query.get(user_id)
    if not user:
        return
    
    # Update specific game progress
    if not hasattr(user, 'language_progress'):
        user.language_progress = '{}'
    
    progress = json.loads(user.language_progress or '{}')
    if game_type not in progress:
        progress[game_type] = {'total_score': 0, 'games_played': 0}
    
    progress[game_type]['total_score'] += score
    progress[game_type]['games_played'] += 1
    progress[game_type]['average'] = progress[game_type]['total_score'] / progress[game_type]['games_played']
    
    user.language_progress = json.dumps(progress)
    
    # Update overall stats
    user.games_played = (user.games_played or 0) + 1
    
    # Calculate overall accuracy
    total_score = sum(p['total_score'] for p in progress.values())
    total_games = sum(p['games_played'] for p in progress.values())
    user.language_accuracy = total_score / total_games if total_games > 0 else 0
    
    db.session.commit()

def calculate_pronunciation_reward(accuracy):
    """Calculate rewards for pronunciation performance"""
    base_reward = 10
    if accuracy >= 95:
        return base_reward * 3
    elif accuracy >= 85:
        return base_reward * 2
    elif accuracy >= 70:
        return base_reward
    else:
        return base_reward // 2

def update_user_rewards(user_id, reward):
    """Update user's language tokens and rewards"""
    user = User.query.get(user_id)
    if not user:
        return
    
    user.language_tokens = (user.language_tokens or 0) + reward
    user.total_points = (user.total_points or 0) + reward
    
    # Check for achievements
    check_language_achievements(user_id)
    
    db.session.commit()

def update_pet_from_learning(user_id, performance_score):
    """Update pet happiness based on learning performance"""
    pet = Pet.query.filter_by(user_id=user_id).first()
    if not pet:
        return
    
    # Calculate happiness increase based on performance
    happiness_increase = max(1, int(performance_score / 20))
    pet.happiness = min(100, (pet.happiness or 50) + happiness_increase)
    
    # Update pet experience
    pet.experience = (pet.experience or 0) + happiness_increase
    
    # Level up pet if enough experience
    if pet.experience >= pet.level * 100:
        pet.level = (pet.level or 1) + 1
        pet.experience = 0
    
    pet.last_interaction = datetime.utcnow()
    db.session.commit()

def get_pronunciation_feedback(accuracy):
    """Generate pronunciation feedback based on accuracy"""
    if accuracy >= 95:
        return "Perfect! Your pronunciation is excellent! 🌟"
    elif accuracy >= 85:
        return "Great job! Your pronunciation is very good! 😊"
    elif accuracy >= 70:
        return "Good effort! Keep practicing to improve! 👍"
    else:
        return "Keep trying! Practice makes perfect! 💪"

def scramble_word(word):
    """Scramble letters in a word"""
    if len(word) <= 2:
        return word
    
    letters = list(word)
    # Keep first and last letter in place for easier solving
    middle = letters[1:-1]
    random.shuffle(middle)
    
    return letters[0] + ''.join(middle) + letters[-1]

def get_story_vocabulary(level, theme):
    """Get vocabulary suggestions for story building"""
    vocab_sets = VOCABULARY_SETS.get(level, {})
    suggestions = []
    
    # Add theme-related words
    if theme == 'adventure':
        suggestions.extend(['journey', 'treasure', 'castle', 'forest', 'brave'])
    elif theme == 'friendship':
        suggestions.extend(['friend', 'kind', 'help', 'share', 'care'])
    elif theme == 'family':
        suggestions.extend(['love', 'home', 'together', 'happy', 'safe'])
    
    # Add general vocabulary
    for category, words in vocab_sets.items():
        suggestions.extend(random.sample(words, min(3, len(words))))
    
    return suggestions[:15]  # Limit to 15 words

def get_min_words_for_level(level):
    """Get minimum word count for story based on level"""
    word_counts = {
        'beginner': 20,
        'intermediate': 50,
        'advanced': 100
    }
    return word_counts.get(level, 20)

def calculate_story_reward(score, word_count):
    """Calculate rewards for story creation"""
    base_reward = 20
    
    # Bonus for good score
    score_bonus = int(score * 0.5)
    
    # Bonus for word count
    word_bonus = min(20, word_count // 10)
    
    return base_reward + score_bonus + word_bonus

def calculate_puzzle_reward(accuracy, puzzle_count):
    """Calculate rewards for puzzle completion"""
    base_reward = 15
    accuracy_bonus = int(accuracy * 0.3)
    puzzle_bonus = puzzle_count * 5
    
    return base_reward + accuracy_bonus + puzzle_bonus

def get_puzzle_feedback(accuracy):
    """Generate puzzle completion feedback"""
    if accuracy >= 90:
        return "Amazing! You're a word puzzle master! 🏆"
    elif accuracy >= 75:
        return "Excellent work! You solved most puzzles! ⭐"
    elif accuracy >= 50:
        return "Good job! Keep practicing to improve! 👍"
    else:
        return "Don't give up! Puzzles help you learn! 💪"

def get_translation_phrases(level, language):
    """Get phrases for translation game"""
    phrases = {
        'beginner': [
            "Hello, how are you?",
            "My name is...",
            "I am happy",
            "Thank you very much",
            "Good morning"
        ],
        'intermediate': [
            "What is your favorite color?",
            "I like to play games",
            "Can you help me please?",
            "Where is the library?",
            "I want to learn more"
        ],
        'advanced': [
            "I enjoy reading books in my free time",
            "What do you want to be when you grow up?",
            "Learning new languages is exciting",
            "Can you tell me about your family?",
            "I hope we can be good friends"
        ]
    }
    
    return phrases.get(level, phrases['beginner'])

def get_phrase_difficulty(phrase):
    """Determine phrase difficulty for scoring"""
    word_count = len(phrase.split())
    if word_count <= 4:
        return 'easy'
    elif word_count <= 8:
        return 'medium'
    else:
        return 'hard'

def check_language_achievements(user_id):
    """Check and award language learning achievements"""
    user = User.query.get(user_id)
    if not user:
        return
    
    achievements_to_check = [
        {'id': 'first_word', 'name': 'First Word', 'condition': lambda u: u.language_tokens >= 10},
        {'id': 'word_collector', 'name': 'Word Collector', 'condition': lambda u: u.language_tokens >= 100},
        {'id': 'pronunciation_pro', 'name': 'Pronunciation Pro', 'condition': lambda u: u.language_accuracy >= 85},
        {'id': 'story_teller', 'name': 'Story Teller', 'condition': lambda u: u.games_played >= 20},
        {'id': 'language_master', 'name': 'Language Master', 'condition': lambda u: u.language_tokens >= 1000}
    ]
    
    for achievement_data in achievements_to_check:
        if achievement_data['condition'](user):
            # Check if user already has this achievement
            existing = Achievement.query.filter_by(
                user_id=user_id, 
                achievement_id=achievement_data['id']
            ).first()
            
            if not existing:
                new_achievement = Achievement(
                    user_id=user_id,
                    achievement_id=achievement_data['id'],
                    name=achievement_data['name'],
                    earned_at=datetime.utcnow()
                )
                db.session.add(new_achievement)
    
    db.session.commit()

def check_story_achievements(user_id, story_text):
    """Check for story-specific achievements"""
    achievements = []
    word_count = len(story_text.split())
    
    if word_count >= 100:
        achievements.append({
            'id': 'long_story',
            'name': 'Long Story Teller',
            'description': 'Wrote a story with 100+ words!'
        })
    
    if word_count >= 200:
        achievements.append({
            'id': 'epic_story',
            'name': 'Epic Story Creator',
            'description': 'Wrote an epic story with 200+ words!'
        })
    
    return achievements