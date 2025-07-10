from flask import current_app
from app.models.emotion import EmotionalState
from app.models.user import User
import json

def analyze_emotion(user_id, message):
    """
    Analyze emotion from a user's message.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    sentiment_score = analyze_sentiment(message)
    emotion = detect_emotion(message, sentiment_score)

    emotion_state = EmotionalState.query.filter_by(user_id=user_id).first()
    if emotion_state:
        emotion_state.update_emotional_metrics({"mood": emotion, "intensity": abs(sentiment_score) * 10})
        db.session.commit()

    return {"emotion": emotion, "sentiment_score": sentiment_score}, 200

def analyze_sentiment(message):
    """
    Analyze sentiment of a message with a simple keyword approach.
    """
    positive_words = ["happy", "joy", "love", "great", "awesome", "fun"]
    negative_words = ["sad", "angry", "hate", "bad", "terrible", "upset"]
    message_lower = message.lower()

    pos_count = sum(1 for word in positive_words if word in message_lower)
    neg_count = sum(1 for word in negative_words if word in message_lower)
    total_words = len(message_lower.split())

    return (pos_count - neg_count) / (total_words + 1) if total_words > 0 else 0

def detect_emotion(message, sentiment_score):
    """
    Detect specific emotion based on message content and sentiment.
    """
    message_lower = message.lower()
    if "happy" in message_lower or "excited" in message_lower or sentiment_score > 0.5:
        return "happy"
    elif "sad" in message_lower or "upset" in message_lower or sentiment_score < -0.5:
        return "sad"
    elif "angry" in message_lower or "mad" in message_lower:
        return "angry"
    elif "worried" in message_lower or "anxious" in message_lower:
        return "anxious"
    elif "confused" in message_lower or "don’t understand" in message_lower:
        return "confused"
    return "neutral"

def get_emotion_history(user_id, days=7):
    """
    Retrieve user's emotion history.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    emotion_state = EmotionalState.query.filter_by(user_id=user_id).first()
    if not emotion_state:
        return {"history": [], "message": "No emotion data"}, 200

    recent_moods = emotion_state.get_recent_moods()[-days * 5:]
    return {"history": recent_moods, "summary": emotion_state.get_emotional_summary()}, 200