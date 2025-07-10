from flask import current_app
from app.models.user import User
from app.models.lesson import Lesson
from app.models.game_progress import GameProgress
import json

def get_adaptive_lessons(user_id):
    """
    Retrieve adaptive lessons based on user's progress and learning style.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    learning_style = user.get_dominant_learning_style()
    preferred_subjects = user.get_preferred_subjects()
    completed_lessons = {p.lesson_id for p in UserProgress.query.filter_by(user_id=user_id).all()}

    lessons = Lesson.query.filter(
        Lesson.subject.in_(preferred_subjects),
        Lesson.style == learning_style,
        ~Lesson.id.in_(completed_lessons)
    ).order_by(Lesson.difficulty_level).limit(5).all()

    response = {
        "learning_style": learning_style,
        "lessons": [lesson.to_dict() for lesson in lessons],
        "recommendation_reason": "Tailored to your learning preferences and progress"
    }
    return response, 200

def update_adaptive_progress(user_id, lesson_id, score, time_spent):
    """
    Update user's adaptive learning progress and adjust learning weights.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        return {"error": "Lesson not found"}, 404

    progress = UserProgress.query.filter_by(user_id=user_id, lesson_id=lesson_id).first()
    if not progress:
        progress = UserProgress(user_id=user_id, lesson_id=lesson_id, score=score, time_spent=time_spent)
    else:
        progress.score = score
        progress.time_spent = time_spent
    db.session.add(progress)

    # Adjust learning weights
    adjustment = 0.1 if score > 80 else -0.1 if score < 50 else 0
    user.adjust_learning_weights(lesson.style, adjustment)
    db.session.commit()

    return {
        "message": "Progress updated",
        "new_weights": user.learning_weights,
        "score": score
    }, 200

def get_learning_style_analysis(user_id):
    """
    Analyze and return the user's learning style preferences.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    style_weights = user.learning_weights
    dominant_style = max(style_weights, key=style_weights.get)
    analysis = {
        "dominant_style": dominant_style,
        "weights": style_weights,
        "description": f"You learn best through {dominant_style} activities!"
    }
    return analysis, 200