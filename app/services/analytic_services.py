from flask import current_app
from app.models.user import User
from app.models.lesson import Lesson
from app.models.game_progress import GameProgress
from app.models.achievement import UserAchievement
import json
from datetime import datetime, timedelta

def get_analytics(user_id):
    """
    Retrieve comprehensive analytics for a user.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    lessons_completed = UserProgress.query.filter_by(user_id=user_id).count()
    games_played = GameProgress.query.filter_by(user_id=user_id).all()
    achievements = UserAchievement.query.filter_by(user_id=user_id).all()

    analytics = {
        "user_stats": {
            "total_points": user.total_points,
            "level": user.level,
            "experience_points": user.experience_points,
            "learning_streak": user.learning_streak,
            "longest_streak": user.longest_streak,
            "total_lessons_completed": lessons_completed,
            "total_time_spent": user.total_time_spent
        },
        "game_stats": {
            "total_games": len(games_played),
            "avg_score": sum(p.score for p in games_played) / len(games_played) if games_played else 0,
            "highest_score": max((p.highest_score for p in games_played), default=0)
        },
        "achievements": [a.to_dict() for a in achievements]
    }
    return analytics, 200

def get_student_progress(student_id):
    """
    Retrieve detailed progress for a student.
    """
    student = User.query.get(student_id)
    if not student:
        return {"error": "Student not found"}, 404

    progress = {
        "lessons": {
            "completed": UserProgress.query.filter_by(user_id=student_id).count(),
            "avg_score": db.session.query(db.func.avg(UserProgress.score)).filter_by(user_id=student_id).scalar() or 0
        },
        "games": {
            "played": GameProgress.query.filter_by(user_id=student_id).count(),
            "avg_score": db.session.query(db.func.avg(GameProgress.score)).filter_by(user_id=student_id).scalar() or 0
        },
        "achievements": UserAchievement.query.filter_by(user_id=student_id).count()
    }
    return progress, 200

def get_usage_trends(user_id, days=30):
    """
    Retrieve usage trends over a specified period.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    cutoff = datetime.utcnow() - timedelta(days=days)
    lessons = UserProgress.query.filter(UserProgress.user_id == user_id, UserProgress.updated_at >= cutoff).all()
    games = GameProgress.query.filter(GameProgress.user_id == user_id, GameProgress.last_played >= cutoff).all()

    trends = {
        "daily_activity": {},
        "lesson_completion": len(lessons),
        "game_sessions": len(games)
    }
    for item in lessons + games:
        date = item.updated_at.date().isoformat() if hasattr(item, 'updated_at') else item.last_played.date().isoformat()
        trends["daily_activity"][date] = trends["daily_activity"].get(date, 0) + 1

    return trends, 200