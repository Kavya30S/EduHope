from flask import flash
import json

def log_activity(user_id, activity_type, details):
    """
    Log user activity for analytics.
    """
    from app import current_app
    log_entry = {
        "user_id": user_id,
        "activity_type": activity_type,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }
    current_app.logger.info(json.dumps(log_entry))

def validate_user_input(input_data, required_fields):
    """
    Validate user input for required fields.
    """
    missing = [field for field in required_fields if not input_data.get(field)]
    if missing:
        flash(f"Missing fields: {', '.join(missing)}")
        return False
    return True

def format_child_friendly