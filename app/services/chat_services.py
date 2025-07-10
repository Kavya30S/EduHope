from flask import current_app
from app.models.chat import ChatMessage, ChatSession
from app.services.emotion_ai_services import analyze_emotion
from app.services.llm_service import generate_text
import json
from datetime import datetime

def process_chat_message(user_id, session_id, message):
    """
    Process a user's chat message and generate an AI response.
    """
    session = ChatSession.query.get(session_id)
    if not session or session.user_id != user_id:
        return {"error": "Invalid session"}, 404

    emotion_data, _ = analyze_emotion(user_id, message)
    prompt = f"Respond playfully to a child: {message} (Emotion: {emotion_data['emotion']})"
    ai_response = generate_text(prompt)

    chat_message = ChatMessage(
        session_id=session_id,
        user_id=user_id,
        content=message,
        is_from_user=True,
        emotion_detected=emotion_data["emotion"],
        sentiment_score=emotion_data["sentiment_score"]
    )
    db.session.add(chat_message)

    ai_message = ChatMessage(
        session_id=session_id,
        user_id=user_id,
        content=ai_response,
        is_from_user=False,
        ai_response_type="playful"
    )
    db.session.add(ai_message)
    session.total_messages += 2
    db.session.commit()

    return {"ai_response": ai_response, "emotion": emotion_data["emotion"]}, 200

def start_chat_session(user_id, chat_type="general"):
    """
    Start a new chat session for the user.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    session = ChatSession(
        user_id=user_id,
        chat_type=chat_type,
        session_name=f"{chat_type.capitalize()} Chat - {datetime.utcnow().strftime('%Y-%m-%d')}"
    )
    db.session.add(session)
    db.session.commit()

    return {"session_id": session.id, "intro": session.get_child_friendly_intro()}, 200

def get_chat_history(user_id, session_id=None):
    """
    Retrieve chat history for a user or specific session.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    if session_id:
        messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at).all()
    else:
        messages = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.created_at.desc()).limit(50).all()

    return [msg.to_dict() for msg in messages], 200