import os
import json
import tempfile
import wave
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
import threading
import time
from datetime import datetime

# Speech recognition and synthesis
try:
    import speech_recognition as sr
    import pyttsx3
    from pydub import AudioSegment
    import librosa
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    logging.warning("Speech libraries not available. Voice features will be limited.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.recognizer = None
        self.tts_engine = None
        self.microphone = None
        self.is_listening = False
        self.voice_patterns = {}
        self.pronunciation_feedback = {}
        self.supported_languages = {
            'en': 'en-US',
            'es': 'es-ES', 
            'fr': 'fr-FR',
            'de': 'de-DE',
            'hi': 'hi-IN',
            'zh': 'zh-CN'
        }
        self.initialize_voice_services()
        
    def initialize_voice_services(self):
        """Initialize speech recognition and synthesis services"""
        if not SPEECH_AVAILABLE:
            logger.warning("Speech libraries not available")
            return
            
        try:
            # Initialize speech recognition
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
            # Initialize text-to-speech
            self.tts_engine = pyttsx3.init()
            
            # Configure TTS for children
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to find a female voice (usually more appealing to children)
                for voice in voices:
                    if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                        
            # Set speech rate and volume for children
            self.tts_engine.setProperty('rate', 150)  # Slower speech for children
            self.tts_engine.setProperty('volume', 0.8)
            
            logger.info("Voice services initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing voice services: {e}")
            SPEECH_AVAILABLE = False
    
    def speak_text(self, text: str, language: str = 'en', emotion: str = 'happy') -> bool:
        """Convert text to speech with emotional context"""
        if not SPEECH_AVAILABLE or not self.tts_engine:
            logger.warning("TTS not available")
            return False
            
        try:
            # Adjust speech parameters based on emotion
            rate, volume = self.get_emotion_parameters(emotion)
            self.tts_engine.setProperty('rate', rate)
            self.tts_engine.setProperty('volume', volume)
            
            # Add emotional expressions to text
            emotional_text = self.add_emotional_expressions(text, emotion)
            
            # Speak the text
            self.tts_engine.say(emotional_text)
            self.tts_engine.runAndWait()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            return False
    
    def get_emotion_parameters(self, emotion: str) -> Tuple[int, float]:
        """Get speech parameters based on emotion"""
        emotion_params = {
            'happy': (160, 0.9),
            'excited': (180, 0.95),
            'calm': (140, 0.7),
            'encouraging': (150, 0.85),
            'gentle': (130, 0.75),
            'playful': (170, 0.9)
        }
        return emotion_params.get(emotion, (150, 0.8))
    
    def add_emotional_expressions(self, text: str, emotion: str) -> str:
        """Add emotional expressions to text"""
        expressions = {
            'happy': ['Yay!', 'Wonderful!', 'Great job!'],
            'excited': ['Wow!', 'Amazing!', 'Fantastic!'],
            'encouraging': ['You can do it!', 'Keep going!', 'You\'re doing great!'],
            'playful': ['Hehe!', 'Fun!', 'Let\'s play!']
        }
        
        if emotion in expressions and not any(exp in text for exp in expressions[emotion]):
            return f"{expressions[emotion][0]} {text}"
        
        return text
    
    def listen_for_speech(self, timeout: float = 5.0, language: str = 'en') -> Optional[str]:
        """Listen for speech input with timeout"""
        if not SPEECH_AVAILABLE or not self.recognizer or not self.microphone:
            logger.warning("Speech recognition not available")
            return None
            
        try:
            with self.microphone as source:
                logger.info("Listening for speech...")
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
            # Convert speech to text
            language_code = self.supported_languages.get(language, 'en-US')
            text = self.recognizer.recognize_google(audio, language=language_code)
            
            logger.info(f"Recognized speech: {text}")
            return text.lower().strip()
            
        except sr.WaitTimeoutError:
            logger.info("Speech recognition timeout")
            return None
        except sr.UnknownValueError:
            logger.info("Could not understand speech")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in speech recognition: {e}")
            return None
    
    def start_continuous_listening(self, callback_func, language: str = 'en'):
        """Start continuous speech recognition in background"""
        if not SPEECH_AVAILABLE:
            return False
            
        def listen_continuously():
            self.is_listening = True
            while self.is_listening:
                try:
                    result = self.listen_for_speech(timeout=2.0, language=language)
                    if result:
                        callback_func(result)
                except Exception as e:
                    logger.error(f"Error in continuous listening: {e}")
                time.sleep(0.5)
        
        # Start listening in a separate thread
        listen_thread = threading.Thread(target=listen_continuously, daemon=True)
        listen_thread.start()
        return True
    
    def stop_continuous_listening(self):
        """Stop continuous speech recognition"""
        self.is_listening = False
    
    def analyze_pronunciation(self, target_word: str, user_audio_path: str, 
                            language: str = 'en') -> Dict:
        """Analyze pronunciation accuracy"""
        if not SPEECH_AVAILABLE:
            return {
                'accuracy_score': 0.5,
                'feedback': "Pronunciation analysis not available",
                'suggestions': []
            }
            
        try:
            # Get user's pronunciation
            user_text = self.transcribe_audio_file(user_audio_path, language)
            
            if not user_text:
                return {
                    'accuracy_score': 0.0,
                    'feedback': "Could not understand your pronunciation. Try speaking more clearly!",
                    'suggestions': ["Speak louder", "Speak more slowly", "Try again"]
                }
            
            # Simple pronunciation analysis
            accuracy = self.calculate_pronunciation_accuracy(target_word, user_text)
            feedback = self.generate_pronunciation_feedback(target_word, user_text, accuracy)
            suggestions = self.get_pronunciation_suggestions(target_word, user_text, accuracy)
            
            return {
                'accuracy_score': accuracy,
                'feedback': feedback,
                'suggestions': suggestions,
                'recognized_text': user_text
            }
            
        except Exception as e:
            logger.error(f"Error analyzing pronunciation: {e}")
            return {
                'accuracy_score': 0.3,
                'feedback': "Let's try that again! Practice makes perfect!",
                'suggestions': ["Keep practicing", "Listen carefully", "Try again"]
            }
    
    def transcribe_audio_file(self, audio_path: str, language: str = 'en') -> Optional[str]:
        """Transcribe audio file to text"""
        if not SPEECH_AVAILABLE or not self.recognizer:
            return None
            
        try:
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
                
            language_code = self.supported_languages.get(language, 'en-US')
            text = self.recognizer.recognize_google(audio, language=language_code)
            
            return text.lower().strip()
            
        except Exception as e:
            logger.error(f"Error transcribing audio file: {e}")
            return None
    
    def calculate_pronunciation_accuracy(self, target: str, recognized: str) -> float:
        """Calculate pronunciation accuracy score"""
        target = target.lower().strip()
        recognized = recognized.lower().strip()
        
        if target == recognized:
            return 1.0
        
        # Simple similarity calculation
        target_words = target.split()
        recognized_words = recognized.split()
        
        if not target_words or not recognized_words:
            return 0.0
        
        # Check if the main word is present
        if target in recognized or any(word in recognized for word in target_words):
            return 0.8
        
        # Character similarity
        common_chars = sum(1 for char in target if char in recognized)
        similarity = common_chars / len(target) if target else 0
        
        return min(0.7, similarity)
    
    def generate_pronunciation_feedback(self, target: str, recognized: str, accuracy: float) -> str:
        """Generate personalized pronunciation feedback"""
        if accuracy >= 0.9:
            return f"Perfect! You said '{target}' beautifully! 🌟"
        elif accuracy >= 0.7:
            return f"Great job! Your pronunciation of '{target}' is very good! 👍"
        elif accuracy >= 0.5:
            return f"Good try! Let's practice '{target}' a bit more. You're getting better! 😊"
        else:
            return f"Let's practice '{target}' together. Listen carefully and try again! 💪"
    
    def get_pronunciation_suggestions(self, target: str, recognized: str, accuracy: float) -> List[str]:
        """Get pronunciation improvement suggestions"""
        suggestions = []
        
        if accuracy < 0.5:
            suggestions.extend([
                "Listen to the word carefully first",
                "Break the word into smaller parts",
                "Speak more slowly and clearly"
            ])
        elif accuracy < 0.8:
            suggestions.extend([
                "Pay attention to each sound",
                "Practice the word a few more times",
                "Try to match the rhythm"
            ])
        else:
            suggestions.extend([
                "You're doing great! Keep practicing",
                "Try saying it in a sentence",
                "Perfect! Ready for the next word?"
            ])
        
        return suggestions
    
    def create_pronunciation_exercise(self, words: List[str], language: str = 'en') -> Dict:
        """Create a pronunciation exercise"""
        exercise = {
            'id': f"pron_ex_{int(time.time())}",
            'words': words,
            'language': language,
            'instructions': "Listen to each word and repeat it clearly.",
            'created_at': datetime.now().isoformat()
        }
        
        return exercise
    
    def generate_voice_games(self, difficulty: str = 'easy', topic: str = 'general') -> Dict:
        """Generate voice-based learning games"""
        games = {
            'easy': {
                'general': {
                    'name': 'Repeat After Me',
                    'description': 'Listen and repeat simple words',
                    'words': ['cat', 'dog', 'sun', 'moon', 'tree', 'book'],
                    'instructions': 'Listen to each word and say it back!'
                },
                'animals': {
                    'name': 'Animal Sounds',
                    'description': 'Say animal names clearly',
                    'words': ['lion', 'elephant', 'bird', 'fish', 'monkey', 'rabbit'],
                    'instructions': 'Name these animals clearly!'
                },
                'colors': {
                    'name': 'Color Names',
                    'description': 'Practice saying color names',
                    'words': ['red', 'blue', 'green', 'yellow', 'purple', 'orange'],
                    'instructions': 'Say these beautiful colors!'
                }
            },
            'medium': {
                'general': {
                    'name': 'Word Builder',
                    'description': 'Practice longer words',
                    'words': ['butterfly', 'rainbow', 'adventure', 'wonderful', 'imagination'],
                    'instructions': 'Try these longer words!'
                },
                'sentences': {
                    'name': 'Sentence Practice',
                    'description': 'Say complete sentences',
                    'words': ['I love learning', 'Books are fun', 'Playing is great', 'Friends are special'],
                    'instructions': 'Say these sentences clearly!'
                }
            },
            'hard': {
                'tongue_twisters': {
                    'name': 'Tongue Twisters',
                    'description': 'Challenge your pronunciation',
                    'words': ['She sells seashells', 'Peter Piper picked', 'Red lorry yellow lorry'],
                    'instructions': 'Try these tongue twisters!'
                }
            }
        }
        
        return games.get(difficulty, {}).get(topic, games['easy']['general'])
    
    def record_user_voice(self, duration: float = 5.0) -> Optional[str]:
        """Record user's voice and save to temporary file"""
        if not SPEECH_AVAILABLE or not self.microphone:
            return None
            
        try:
            with self.microphone as source:
                logger.info(f"Recording for {duration} seconds...")
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=duration)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            with open(temp_file.name, 'wb') as f:
                f.write(audio.get_wav_data())
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error recording voice: {e}")
            return None
    
    def analyze_speech_patterns(self, user_id: int, audio_path: str) -> Dict:
        """Analyze user's speech patterns for personalized learning"""
        try:
            if user_id not in self.voice_patterns:
                self.voice_patterns[user_id] = {
                    'clarity_scores': [],
                    'confidence_scores': [],
                    'preferred_pace': 'normal',
                    'common_mistakes': [],
                    'improvement_areas': [],
                    'last_analysis': datetime.now()
                }
            
            # Simple analysis (in real implementation, would use more sophisticated audio analysis)
            patterns = self.voice_patterns[user_id]
            
            # Simulate analysis results
            clarity_score = np.random.uniform(0.6, 0.9)  # In real app, would analyze actual audio
            confidence_score = np.random.uniform(0.5, 0.8)
            
            patterns['clarity_scores'].append(clarity_score)
            patterns['confidence_scores'].append(confidence_score)
            patterns['last_analysis'] = datetime.now()
            
            # Keep only recent scores
            if len(patterns['clarity_scores']) > 10:
                patterns['clarity_scores'] = patterns['clarity_scores'][-10:]
            if len(patterns['confidence_scores']) > 10:
                patterns['confidence_scores'] = patterns['confidence_scores'][-10:]
            
            return {
                'clarity_score': clarity_score,
                'confidence_score': confidence_score,
                'improvement_trend': self.calculate_improvement_trend(patterns),
                'recommendations': self.get_speech_recommendations(patterns)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing speech patterns: {e}")
            return {
                'clarity_score': 0.7,
                'confidence_score': 0.6,
                'improvement_trend': 'stable',
                'recommendations': ['Keep practicing!']
            }
    
    def calculate_improvement_trend(self, patterns: Dict) -> str:
        """Calculate if user is improving over time"""
        if len(patterns['clarity_scores']) < 3:
            return 'learning'
        
        recent_scores = patterns['clarity_scores'][-3:]
        older_scores = patterns['clarity_scores'][-6:-3] if len(patterns['clarity_scores']) >= 6 else []
        
        if not older_scores:
            return 'learning'
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)
        
        if recent_avg > older_avg + 0.1:
            return 'improving'
        elif recent_avg < older_avg - 0.1:
            return 'needs_practice'
        else:
            return 'stable'
    
    def get_speech_recommendations(self, patterns: Dict) -> List[str]:
        """Get personalized speech improvement recommendations"""
        recommendations = []
        
        if patterns['clarity_scores']:
            avg_clarity = sum(patterns['clarity_scores']) / len(patterns['clarity_scores'])
            if avg_clarity < 0.6:
                recommendations.extend([
                    "Try speaking more slowly",
                    "Make sure to pronounce each sound clearly",
                    "Practice in a quiet place"
                ])
            elif avg_clarity > 0.8:
                recommendations.extend([
                    "Great job! You're speaking very clearly!",
                    "Ready for more challenging words?",
                    "Try some tongue twisters!"
                ])
        
        if patterns['confidence_scores']:
            avg_confidence = sum(patterns['confidence_scores']) / len(patterns['confidence_scores'])
            if avg_confidence < 0.5:
                recommendations.extend([
                    "Don't worry about mistakes - they help you learn!",
                    "Practice with your favorite words first",
                    "Remember, you're doing great!"
                ])
        
        if not recommendations:
            recommendations = ["Keep up the great work!", "Practice makes perfect!"]
        
        return recommendations
    
    def create_personalized_voice_lesson(self, user_id: int, topic: str = 'general') -> Dict:
        """Create a personalized voice lesson based on user's progress"""
        patterns = self.voice_patterns.get(user_id, {})
        
        # Determine difficulty based on user's performance
        if patterns and patterns.get('clarity_scores'):
            avg_clarity = sum(patterns['clarity_scores']) / len(patterns['clarity_scores'])
            if avg_clarity < 0.6:
                difficulty = 'easy'
            elif avg_clarity > 0.8:
                difficulty = 'hard'
            else:
                difficulty = 'medium'
        else:
            difficulty = 'easy'
        
        # Generate lesson content
        lesson = {
            'id': f"voice_lesson_{user_id}_{int(time.time())}",
            'user_id': user_id,
            'topic': topic,
            'difficulty': difficulty,
            'exercises': [],
            'estimated_duration': 10,  # minutes
            'created_at': datetime.now().isoformat()
        }
        
        # Add exercises based on difficulty and patterns
        if difficulty == 'easy':
            lesson['exercises'] = [
                {
                    'type': 'word_repetition',
                    'words': ['hello', 'friend', 'happy', 'smile', 'love'],
                    'instruction': 'Repeat these happy words!'
                },
                {
                    'type': 'simple_phrases',
                    'phrases': ['Good morning', 'Thank you', 'Please help me'],
                    'instruction': 'Practice these useful phrases!'
                }
            ]
        elif difficulty == 'medium':
            lesson['exercises'] = [
                {
                    'type': 'story_reading',
                    'text': 'Once upon a time, in a magical forest, lived a friendly dragon who loved to help children learn.',
                    'instruction': 'Read this story aloud with expression!'
                },
                {
                    'type': 'question_answering',
                    'questions': ['What is your favorite color?', 'What do you like to do for fun?'],
                    'instruction': 'Answer these questions in complete sentences!'
                }
            ]
        else:  # hard
            lesson['exercises'] = [
                {
                    'type': 'tongue_twisters',
                    'twisters': ['She sells seashells by the seashore', 'How much wood would a woodchuck chuck'],
                    'instruction': 'Challenge yourself with these tongue twisters!'
                },
                {
                    'type': 'improvisation',
                    'prompts': ['Tell a story about a magic pencil', 'Describe your dream adventure'],
                    'instruction': 'Use your imagination and speak freely!'
                }
            ]
        
        return lesson
    
    def provide_emotional_voice_support(self, emotion: str, user_message: str = '') -> str:
        """Provide emotional support through voice"""
        support_messages = {
            'sad': [
                "It's okay to feel sad sometimes. You're brave and strong! 🌈",
                "Even on cloudy days, the sun is still shining above the clouds. You matter! ☀️",
                "Feelings come and go like waves. This sad feeling will pass, and happy ones will come! 🌊"
            ],
            'angry': [
                "When we feel angry, let's take three deep breaths together. Inhale... exhale... 🌬️",
                "It's normal to feel upset sometimes. Let's find a way to feel better together! 🤗",
                "Anger is like a storm - it feels big, but it always passes. You're safe! ⛈️➡️🌤️"
            ],
            'scared': [
                "You are braver than you believe and stronger than you think! 🦁",
                "When we're scared, we can think of happy things. What makes you smile? 😊",
                "Every brave person feels scared sometimes. That's what makes them brave! 🛡️"
            ],
            'happy': [
                "Your happiness is like sunshine - it brightens everything around you! ☀️",
                "I love seeing you happy! Your joy is contagious! 😄",
                "Happy feelings are wonderful! Let's celebrate this moment! 🎉"
            ],
            'worried': [
                "Worries are like clouds - they look big but they always move away! ☁️",
                "Let's think of one thing that makes you feel safe and happy! 🏠",
                "You don't have to carry your worries alone. I'm here with you! 🤝"
            ]
        }
        
        messages = support_messages.get(emotion, support_messages['happy'])
        selected_message = np.random.choice(messages)
        
        # Speak the supportive message
        self.speak_text(selected_message, emotion=emotion)
        
        return selected_message
    
    def get_voice_statistics(self, user_id: int) -> Dict:
        """Get voice usage statistics for a user"""
        if user_id not in self.voice_patterns:
            return {
                'total_sessions': 0,
                'average_clarity': 0,
                'improvement_rate': 0,
                'favorite_activities': []
            }
        
        patterns = self.voice_patterns[user_id]
        
        return {
            'total_sessions': len(patterns.get('clarity_scores', [])),
            'average_clarity': sum(patterns.get('clarity_scores', [0])) / max(1, len(patterns.get('clarity_scores', [1]))),
            'average_confidence': sum(patterns.get('confidence_scores', [0])) / max(1, len(patterns.get('confidence_scores', [1]))),
            'improvement_trend': self.calculate_improvement_trend(patterns),
            'last_activity': patterns.get('last_analysis'),
            'recommendations': self.get_speech_recommendations(patterns)
        }
    
    def cleanup_temp_files(self):
        """Clean up temporary audio files"""
        try:
            temp_dir = tempfile.gettempdir()
            for filename in os.listdir(temp_dir):
                if filename.endswith('.wav') and 'speech_' in filename:
                    file_path = os.path.join(temp_dir, filename)
                    if os.path.getctime(file_path) < time.time() - 3600:  # Older than 1 hour
                        os.remove(file_path)
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")

# Global instance
voice_service = VoiceService()