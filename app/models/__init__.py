"""
EduHope Services Package
Provides AI-powered services for personalized learning, emotional support, and content generation.
"""

# Import models used across service modules
from app.models.achievement import Achievement, UserAchievement, AchievementCategory
from app.models.chat import ChatMessage, ChatSession, ChatType, EmotionLevel
from app.models.emotion import EmotionalState, SupportSession
from app.models.game_progress import GameProgress
from app.models.lesson import Lesson, LessonFeedback, UserProgress as LessonUserProgress
from app.models.pet import Pet
from app.models.pet_accessory import PetAccessory, UserPetAccessory
from app.models.social import (
    SocialActivity, SocialGroup, FriendRequest, Friendship,
    GroupMember, Chat, ChatReaction
)
from app.models.story import Story, StoryCollaboration, StoryProgress, StoryRating
from app.models.user import User, UserProgress, LearningSession

# Optionally: Define what gets exported on `from app.services import *`
__all__ = [
    "Achievement", "UserAchievement", "AchievementCategory",
    "ChatMessage", "ChatSession", "ChatType", "EmotionLevel",
    "EmotionalState", "SupportSession",
    "GameProgress",
    "Lesson", "LessonFeedback", "LessonUserProgress",
    "Pet",
    "PetAccessory", "UserPetAccessory",
    "SocialActivity", "SocialGroup", "FriendRequest", "Friendship",
    "GroupMember", "Chat", "ChatReaction",
    "Story", "StoryCollaboration", "StoryProgress", "StoryRating",
    "User", "UserProgress", "LearningSession"
]
