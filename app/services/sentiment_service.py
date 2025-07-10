import os
import json
import numpy as np
from typing import Dict, List, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import librosa
import SpeechRecognition as sr
from scipy.signal import butter, lfilter
from sklearn.preprocessing import StandardScaler
from datetime import datetime
from app import db, create_app
from app.models.emotion import EmotionalState
from app.config import Config
from utils.helpers import get_current_time, get_random_emoji, translate_text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SentimentService:
    """Service for analyzing sentiment from text and voice inputs, tailored for children."""

    def __init__(self):
        """Initialize sentiment analyzer, audio processing tools, and load datasets."""
        self.analyzer = SentimentIntensityAnalyzer()
        self.recognizer = sr.Recognizer()
        self.scaler = StandardScaler()
        self.emotion_thresholds = {
            'positive': 0.3,
            'neutral': -0.3,
            'negative': -0.3
        }
        self.sampling_rate = 16000
        self.lowcut = 300.0
        self.highcut = 3400.0
        self.order = 5
        self.app = create_app()
        with self.app.app_context():
            self.config = Config()
            self.health_facts = self._load_dataset('who')
            self.story_prompts = self._load_dataset('wikitext')

    def _load_dataset(self, dataset_type: str) -> List[str]:
        """Load a dataset from the configured path into a list of lines."""
        path = self.config.get_dataset_path(dataset_type)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        logger.warning(f"Dataset {dataset_type} not found at {path}")
        return []

    def butter_bandpass(self, lowcut: float, highcut: float, fs: float, order: int) -> tuple:
        """Design a Butterworth bandpass filter."""
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(order, [low, high], btype='band')
        return b, a

    def bandpass_filter(self, data: np.ndarray, lowcut: float, highcut: float, fs: float, order: int) -> np.ndarray:
        """Apply a bandpass filter to audio data."""
        b, a = self.butter_bandpass(lowcut, highcut, fs, order)
        y = lfilter(b, a, data)
        return y

    def extract_audio_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Extract features from audio data for sentiment analysis."""
        features = {}
        mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
        features['mfcc_mean'] = np.mean(mfccs, axis=1)
        features['mfcc_std'] = np.std(mfccs, axis=1)
        chroma = librosa.feature.chroma_stft(y=audio_data, sr=sample_rate)
        features['chroma_mean'] = np.mean(chroma, axis=1)
        features['chroma_std'] = np.std(chroma, axis=1)
        contrast = librosa.feature.spectral_contrast(y=audio_data, sr=sample_rate)
        features['contrast_mean'] = np.mean(contrast, axis=1)
        features['contrast_std'] = np.std(contrast, axis=1)
        return features

    def analyze_voice_sentiment(self, audio_file_path: str) -> Dict[str, Any]:
        """Analyze sentiment from an audio file."""
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
                audio_data = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
                audio_data = audio_data.astype(np.float32) / 32768.0
                filtered_data = self.bandpass_filter(audio_data, self.lowcut, self.highcut, self.sampling_rate, self.order)
                features = self.extract_audio_features(filtered_data, self.sampling_rate)
                scaled_features = self.scaler.fit_transform([list(features.values())[0]])
                energy = np.mean(np.abs(filtered_data))
                pitch, _ = librosa.piptrack(y=filtered_data, sr=self.sampling_rate)
                pitch_mean = np.mean(pitch[pitch > 0])
                sentiment_score = self._map_audio_to_sentiment(energy, pitch_mean)
                mood = self._determine_mood(sentiment_score)
                return {
                    'sentiment_score': sentiment_score,
                    'mood': mood,
                    'confidence': 0.85 if energy > 0.1 else 0.6,
                    'features': features
                }
        except Exception as e:
            logger.error(f"Voice analysis failed: {str(e)}")
            return {'sentiment_score': 0.0, 'mood': 'neutral', 'confidence': 0.5, 'error': str(e)}

    def _map_audio_to_sentiment(self, energy: float, pitch_mean: float) -> float:
        """Map audio features to a sentiment score."""
        base_score = (energy * 0.7 + (pitch_mean / 500.0) * 0.3) - 0.5
        return max(min(base_score, 1.0), -1.0)

    def analyze_text_sentiment(self, text: str, language: str = 'en') -> Dict[str, Any]:
        """Analyze sentiment from text input, considering health or story context."""
        try:
            cleaned_text = profanity.censor(text)
            if language != 'en':
                cleaned_text = translate_text(cleaned_text, language)
            sentiment = self.analyzer.polarity_scores(cleaned_text)
            compound_score = sentiment['compound']
            mood = self._determine_mood(compound_score)
            # Contextual enhancement with datasets
            context_score = self._get_contextual_sentiment(cleaned_text)
            adjusted_score = (compound_score + context_score) / 2
            return {
                'sentiment_score': adjusted_score,
                'mood': self._determine_mood(adjusted_score),
                'positive': sentiment['pos'],
                'negative': sentiment['neg'],
                'neutral': sentiment['neu'],
                'confidence': 0.9 if abs(compound_score) > 0.2 else 0.7
            }
        except Exception as e:
            logger.error(f"Text sentiment analysis failed: {str(e)}")
            return {'sentiment_score': 0.0, 'mood': 'neutral', 'confidence': 0.5, 'error': str(e)}

    def _get_contextual_sentiment(self, text: str) -> float:
        """Adjust sentiment based on health or story context from datasets."""
        text_lower = text.lower()
        health_match = any(fact.lower() in text_lower for fact in self.health_facts)
        story_match = any(prompt.lower() in text_lower for prompt in self.story_prompts)
        if health_match:
            return 0.2  # Positive boost for health-related content
        elif story_match:
            return 0.1  # Slight positive boost for story-related content
        return 0.0

    def _determine_mood(self, score: float) -> str:
        """Determine mood based on sentiment score."""
        if score >= self.emotion_thresholds['positive']:
            return 'happy'
        elif score <= self.emotion_thresholds['negative']:
            return 'sad'
        else:
            return 'neutral'

    def update_emotional_state(self, user_id: int, sentiment_data: Dict[str, Any]) -> None:
        """Update user's emotional state in the database."""
        try:
            emotional_state = EmotionalState.query.filter_by(user_id=user_id).first()
            if not emotional_state:
                emotional_state = EmotionalState(user_id=user_id)
                db.session.add(emotional_state)
            mood = sentiment_data.get('mood', 'neutral')
            intensity = self._calculate_intensity(sentiment_data.get('sentiment_score', 0.0))
            emotional_state.happiness = max(0, min(100, emotional_state.happiness + (10 if mood == 'happy' else -5 if mood == 'sad' else 0) * intensity))
            emotional_state.stress_level = max(0, min(100, emotional_state.stress_level + (5 if mood == 'sad' else -5 if mood == 'happy' else 0) * intensity))
            emotional_state.last_check_in = datetime.utcnow()
            moods = json.loads(emotional_state.recent_moods or '[]')
            moods.append({
                'timestamp': get_current_time(),
                'mood': mood,
                'intensity': intensity,
                'source': 'voice' if 'audio_features' in sentiment_data else 'text'
            })
            if len(moods) > 50:
                moods = moods[-50:]
            emotional_state.recent_moods = json.dumps(moods)
            db.session.commit()
            logger.info(f"Updated emotional state for user {user_id}: {mood}")
        except Exception as e:
            logger.error(f"Failed to update emotional state: {str(e)}")
            db.session.rollback()

    def _calculate_intensity(self, score: float) -> float:
        """Calculate intensity based on sentiment score."""
        return max(0.5, min(1.5, abs(score) * 2))

    def get_emotional_feedback(self, user_id: int) -> Dict[str, Any]:
        """Generate child-friendly feedback based on emotional state."""
        emotional_state = EmotionalState.query.filter_by(user_id=user_id).first()
        if not emotional_state:
            return {'message': "😊 Let's start a fun journey!", 'recommendation': 'play_with_pet'}
        summary = {
            'happiness': emotional_state.happiness,
            'stress_level': emotional_state.stress_level,
            'recent_mood': json.loads(emotional_state.recent_moods or '[]')[-1]['mood'] if emotional_state.recent_moods else 'neutral'
        }
        feedback = {
            'happy': f"🎉 You're super happy! {get_random_emoji()} Keep shining!",
            'sad': f"💙 Oh no, feeling sad? Let's play with your pet! {get_random_emoji()}",
            'neutral': f"😊 You're doing great! Want to learn something new? {get_random_emoji()}"
        }
        recommendations = {
            'happy': 'explore_lesson',
            'sad': 'interact_pet',
            'neutral': 'play_game'
        }
        return {
            'message': feedback.get(summary['recent_mood'], "🌟 Let's have fun together!"),
            'recommendation': recommendations.get(summary['recent_mood'], 'interact_pet'),
            'summary': summary
        }

    def save_audio_analysis(self, user_id: int, audio_file_path: str) -> bool:
        """Save audio analysis results for future reference."""
        try:
            sentiment_data = self.analyze_voice_sentiment(audio_file_path)
            with open(f'instance/audio_analysis_{user_id}_{get_current_time()}.json', 'w') as f:
                json.dump(sentiment_data, f, indent=4)
            self.update_emotional_state(user_id, sentiment_data)
            return True
        except Exception as e:
            logger.error(f"Failed to save audio analysis: {str(e)}")
            return False

    def get_historical_emotions(self, user_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """Retrieve historical emotional data for a user."""
        emotional_state = EmotionalState.query.filter_by(user_id=user_id).first()
        if not emotional_state:
            return []
        moods = json.loads(emotional_state.recent_moods or '[]')
        cutoff = datetime.now() - datetime.timedelta(days=days)
        return [m for m in moods if datetime.strptime(m['timestamp'], "%Y-%m-%d %H:%M:%S") > cutoff]

if __name__ == "__main__":
    service = SentimentService()
    sample_text = "I feel so happy because I drank water and ate an apple!"
    text_result = service.analyze_text_sentiment(sample_text)
    print(f"Text Sentiment: {text_result}")