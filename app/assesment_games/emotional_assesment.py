from flask import current_app
from app.models.emotion import EmotionalState
from app.models.chat import ChatMessage
from app.services.emotion_ai_services import analyze_emotion
import json
from datetime import datetime, timedelta

def assess_emotional_state(user_id):
    """
    Assess the emotional state of a user based on recent interactions.
    """
    user_emotion = EmotionalState.query.filter_by(user_id=user_id).first()
    if not user_emotion:
        user_emotion = EmotionalState(user_id=user_id)
        db.session.add(user_emotion)
        db.session.commit()

    # Get recent chat messages (last 7 days)
    recent_messages = ChatMessage.get_user_emotion_history(user_id, days=7)
    if not recent_messages:
        return {"message": "No recent interactions to assess", "state": user_emotion.to_dict()}, 200

    # Analyze emotions from messages
    emotion_counts = {}
    total_sentiment = 0
    for msg in recent_messages:
        emotion = msg.emotion_detected.value if msg.emotion_detected else "neutral"
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        total_sentiment += msg.sentiment_score or 0

    avg_sentiment = total_sentiment / len(recent_messages) if recent_messages else 0
    dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"

    # Update emotional state
    mood_data = {"mood": dominant_emotion, "intensity": 5, "context": "chat_history"}
    user_emotion.add_mood_entry(mood_data)
    db.session.commit()

    # Prepare response with recommendations
    summary = user_emotion.get_emotional_summary()
    response = {
        "dominant_emotion": dominant_emotion,
        "average_sentiment": round(avg_sentiment, 2),
        "emotional_summary": summary,
        "recent_moods": user_emotion.get_recent_moods()[-5:]
    }
    return response, 200

def log_emotional_interaction(user_id, interaction_type, content):
    """
    Log an emotional interaction and update the user's emotional state.
    """
    emotion_result, status = analyze_emotion(user_id, content)
    if status != 200:
        return emotion_result, status

    user_emotion = EmotionalState.query.filter_by(user_id=user_id).first()
    if not user_emotion:
        user_emotion = EmotionalState(user_id=user_id)
        db.session.add(user_emotion)

    mood_data = {
        "mood": emotion_result["emotion"],
        "intensity": abs(emotion_result["sentiment_score"]) * 10,
        "context": interaction_type
    }
    user_emotion.add_mood_entry(mood_data)
    db.session.commit()

    return {"message": "Emotional interaction logged", "emotion": emotion_result}, 200

def get_emotional_trends(user_id, days=30):
    """
    Retrieve emotional trends over a specified period.
    """
    user_emotion = EmotionalState.query.filter_by(user_id=user_id).first()
    if not user_emotion:
        return {"error": "No emotional data found"}, 404

    cutoff_date = datetime.utcnow() - timedelta(days=days)
    recent_moods = [mood for mood in user_emotion.get_recent_moods() if datetime.fromisoformat(mood["timestamp"]) >= cutoff_date]

    trends = {
        "happiness_trend": [],
        "stress_trend": [],
        "mood_frequency": {}
    }
    for mood in recent_moods:
        trends["happiness_trend"].append({"date": mood["timestamp"], "value": user_emotion.happiness})
        trends["stress_trend"].append({"date": mood["timestamp"], "value": user_emotion.stress_level})
        trends["mood_frequency"][mood["mood"]] = trends["mood_frequency"].get(mood["mood"], 0) + 1

    return {"trends": trends, "summary": user_emotion.get_emotional_summary()}, 200