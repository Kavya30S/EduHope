from flask import current_app
from better_profanity import profanity
import json

def moderate_content(content):
    """
    Moderate content for profanity and inappropriate language.
    """
    return profanity.censor(content, censor_char="🌟")

def check_content_safety(content):
    """
    Check if content is safe for children.
    """
    unsafe_keywords = ["violence", "drugs", "hate", "bully", "scary", "danger"]
    content_lower = content.lower()
    return not any(keyword in content_lower for keyword in unsafe_keywords)

def get_moderation_report(content):
    """
    Generate a detailed moderation report.
    """
    censored = moderate_content(content)
    is_safe = check_content_safety(censored)
    report = {
        "original_content": content,
        "censored_content": censored,
        "is_safe": is_safe,
        "unsafe_words": [word for word in content.lower().split() if word in ["violence", "drugs", "hate"]]
    }
    return report

def flag_content(user_id, content, reason):
    """
    Flag content for review by moderators.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    report = {
        "user_id": user_id,
        "content": content,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending"
    }
    # Placeholder for saving to a moderation queue (e.g., database or log)
    current_app.logger.info(json.dumps(report))
    return {"message": "Content flagged for review"}, 200