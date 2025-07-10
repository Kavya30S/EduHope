from flask import current_app
from app.models.lesson import Lesson
from app.models.user import User
from app.models.game_progress import GameProgress
from app.models.achievement import Achievement, UserAchievement
import json

def get_education_content(user_id):
    """
    Retrieve educational content tailored to the user.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    preferred_subjects = user.get_preferred_subjects()
    lessons = Lesson.query.filter(Lesson.subject.in_(preferred_subjects)).order_by(Lesson.difficulty_level).all()
    game_progress = GameProgress.query.filter_by(user_id=user_id).all()
    achievements = UserAchievement.query.filter_by(user_id=user_id).all()

    response = {
        "lessons": [lesson.to_dict() for lesson in lessons],
        "game_progress": [progress.to_dict() for progress in game_progress],
        "achievements": [ach.achievement.to_dict() for ach in achievements]
    }
    return response, 200

def update_education_progress(user_id, lesson_id, score, time_spent):
    """
    Update user's education progress and check for achievements.
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
        user.total_lessons_completed += 1
    else:
        progress.score = score
        progress.time_spent = time_spent
    db.session.add(progress)

    # Update user stats
    user.total_points += score
    user.experience_points += int(score / 2)
    user.total_time_spent += time_spent
    check_level_up(user)

    # Check achievements
    achievements = Achievement.query.filter_by(category="learning").all()
    for ach in achievements:
        if ach.check_requirements(user.get_stats()) and not UserAchievement.query.filter_by(user_id=user_id, achievement_id=ach.id).first():
            user_ach = UserAchievement(user_id=user_id, achievement_id=ach.id)
            db.session.add(user_ach)

    db.session.commit()
    return {"message": "Progress updated", "new_points": user.total_points}, 200

def check_level_up(user):
    """
    Check if the user should level up based on experience points.
    """
    required_exp = user.level * 1000
    if user.experience_points >= required_exp:
        user.level += 1
        user.experience_points -= required_exp
        db.session.commit()

def get_user_stats(user_id):
    """
    Retrieve user's educational statistics.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    return user.get_stats(), 200