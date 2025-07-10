from flask import current_app
from app.models.chat import ChatMessage
from app.models.user import User
from app.services.llm_service import generate_text
import json

def get_support_messages(user_id):
    """
    Retrieve user's support messages.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    messages = ChatMessage.query.filter_by(user_id=user_id, ai_response_type="support").order_by(ChatMessage.created_at.desc()).limit(20).all()
    return [msg.to_dict() for msg in messages], 200

def send_support_message(user_id, message):
    """
    Send a support message and get an AI response.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    prompt = f"Provide a supportive response to a child: {message}"
    ai_response = generate_text(prompt)

    user_msg = ChatMessage(
        session_id=None,
        user_id=user_id,
        content=message,
        is_from_user=True,
        ai_response_type="support"
    )
    ai_msg = ChatMessage(
        session_id=None,
        user_id=user_id,
        content=ai_response,
        is_from_user=False,
        ai_response_type="support"
    )
    db.session.add_all([user_msg, ai_msg])
    db.session.commit()

    return {"message": "Support message sent", "response": ai_response}, 200

def get_support_response(user_id, issue):
    """
    Generate a support response for a specific issue.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    prompt = f"Help a child with this issue: {issue}"
    response = generate_text(prompt)
    return {"support_response": response}, 200