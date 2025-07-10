from flask import current_app
from app.models.chat import ChatMessage
from app.services.emotion_ai_services import analyze_emotion
from app.services.llm_service import generate_text
import json

def process_realtime_message(user_id, message):
    """
    Process a real-time message and respond instantly.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    emotion_data, _ = analyze_emotion(user_id, message)
    prompt = f"Respond in real-time to a child: {message} (Emotion: {emotion_data['emotion']})"
    ai_response = generate_text(prompt, max_length=50)

    chat_message = ChatMessage(
        session_id=None,
        user_id=user_id,
        content=message,
        is_from_user=True,
        emotion_detected=emotion_data["emotion"]
    )
    db.session.add(chat_message)

    ai_message = ChatMessage(
        session_id=None,
        user_id=user_id,
        content=ai_response,
        is_from_user=False,
        ai_response_type="realtime"
    )
    db.session.add(ai_message)
    db.session.commit()

    return {"ai_response": ai_response, "emotion": emotion_data["emotion"]}, 200

def get_realtime_stats(user_id):
    """
    Retrieve real-time interaction stats.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    recent_messages = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.created_at.desc()).limit(10).all()
    stats = {
        "message_count": len(recent_messages),
        "avg_sentiment": sum((m.sentiment_score or 0) for m in recent_messages) / len(recent_messages) if recent_messages else 0
    }
    return stats, 200

def simulate_realtime_event(user_id, event_type):
    """
    Simulate a real-time event for the user.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    if event_type == "pet_alert":
        pet = Pet.query.filter_by(user_id=user_id).first()
        message = f"🐾 {pet.name} wants to play with you!"
    else:
        message = "🌟 Something exciting is happening!"

    return {"event_message": message}, 200