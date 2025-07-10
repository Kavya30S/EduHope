from flask import current_app
from app.models.lesson import Lesson
from app.models.game_progress import GameProgress
from app.models.user import User
import json
from datetime import datetime

def assess_knowledge(user_id, subject=None):
    """
    Assess the user's knowledge based on completed lessons and games.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    # Filter lessons and games by subject if provided
    lessons = Lesson.query.filter(Lesson.subject == subject).all() if subject else Lesson.query.all()
    game_progress = GameProgress.query.filter_by(user_id=user_id).filter(GameProgress.game_type == subject).all() if subject else GameProgress.query.filter_by(user_id=user_id).all()

    # Calculate knowledge metrics
    total_lessons = len(lessons)
    completed_lessons = sum(1 for lesson in lessons if UserProgress.query.filter_by(user_id=user_id, lesson_id=lesson.id).first())
    lesson_completion_rate = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

    total_score = sum(progress.score for progress in game_progress)
    avg_score = total_score / len(game_progress) if game_progress else 0

    # Prepare assessment report
    report = {
        "subject": subject or "All Subjects",
        "lesson_completion": {
            "completed": completed_lessons,
            "total": total_lessons,
            "rate": round(lesson_completion_rate, 2)
        },
        "game_performance": {
            "total_score": total_score,
            "average_score": round(avg_score, 2),
            "games_played": len(game_progress)
        },
        "recommendations": generate_recommendations(user_id, subject)
    }
    return report, 200

def generate_recommendations(user_id, subject):
    """
    Generate learning recommendations based on knowledge assessment.
    """
    user = User.query.get(user_id)
    if not user:
        return []

    completed_lessons = UserProgress.query.filter_by(user_id=user_id).all()
    completed_ids = {progress.lesson_id for progress in completed_lessons}

    # Recommend uncompleted lessons
    uncompleted_lessons = Lesson.query.filter(~Lesson.id.in_(completed_ids))
    if subject:
        uncompleted_lessons = uncompleted_lessons.filter(Lesson.subject == subject)
    uncompleted_lessons = uncompleted_lessons.limit(3).all()

    recommendations = [
        {
            "type": "lesson",
            "title": lesson.title,
            "subject": lesson.subject,
            "difficulty": lesson.difficulty_level,
            "description": lesson.get_child_friendly_description()
        } for lesson in uncompleted_lessons
    ]
    return recommendations

def update_knowledge_progress(user_id, activity_type, activity_id, score):
    """
    Update user's knowledge progress after an activity.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    if activity_type == "lesson":
        lesson = Lesson.query.get(activity_id)
        if not lesson:
            return {"error": "Lesson not found"}, 404
        progress = UserProgress.query.filter_by(user_id=user_id, lesson_id=activity_id).first()
        if not progress:
            progress = UserProgress(user_id=user_id, lesson_id=activity_id, score=score)
        else:
            progress.score = score
        db.session.add(progress)
    elif activity_type == "game":
        progress = GameProgress.query.filter_by(user_id=user_id, game_type=activity_id).first()
        if not progress:
            progress = GameProgress(user_id=user_id, game_type=activity_id)
        progress.update_progress(score=score, time_spent=60, success=score > 50)
        db.session.add(progress)

    db.session.commit()
    return {"message": "Knowledge progress updated"}, 200