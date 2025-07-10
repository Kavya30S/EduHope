import unittest
from app import create_app, db
from app.models.user import User
from app.models.pet import Pet
from app.models.lesson import Lesson
from app.models.emotion import EmotionalState  # Corrected from 'Emotion'
from app.models.game_progress import GameProgress
from app.models.achievement import Achievement
from app.models.pet_accessory import PetAccessory
from app.models.story import Story  # Keeping only defined models
from utils.helpers import is_valid_email, is_valid_password, generate_child_friendly_message
from datetime import datetime

class EduHopeTestCase(unittest.TestCase):
    """Test suite for EduHope core functionalities."""

    def setUp(self):
        """Set up test environment with in-memory database."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            # Create a test user
            user = User(
                username='testkid',
                email='testkid@example.com',
                full_name='Test Kid',
                age=8,
                preferred_language='en',
                culture='Middle Eastern'
            )
            user.set_password('Test1234')
            db.session.add(user)
            db.session.commit()
            self.user = user

    def tearDown(self):
        """Clean up after each test."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_creation(self):
        """Test user creation and password validation."""
        with self.app.app_context():
            user = User.query.filter_by(username='testkid').first()
            self.assertIsNotNone(user)
            self.assertTrue(user.check_password('Test1234'))
            self.assertEqual(user.full_name, 'Test Kid')
            self.assertEqual(user.age, 8)
            self.assertEqual(user.preferred_language, 'en')
            self.assertEqual(user.culture, 'Middle Eastern')
            # Test invalid password
            self.assertFalse(user.check_password('wrongpass'))

    def test_pet_creation(self):
        """Test pet creation and initial state."""
        with self.app.app_context():
            pet = Pet(user_id=self.user.id, name='TestDragon', pet_type='Dragon')
            db.session.add(pet)
            db.session.commit()
            self.assertEqual(Pet.query.count(), 1)
            self.assertEqual(pet.name, 'TestDragon')
            self.assertEqual(pet.pet_type, 'Dragon')
            self.assertEqual(pet.hunger, 50)  # Default hunger value
            self.assertEqual(pet.happiness, 50)  # Default happiness value
            # Test pet feeding
            pet.feed('regular')
            self.assertLess(pet.hunger, 50)
            self.assertGreater(pet.happiness, 50)

    def test_lesson_creation(self):
        """Test lesson creation and retrieval."""
        with self.app.app_context():
            lesson = Lesson(
                title='Counting Stars',
                subject='Math',
                age_group='4-6',
                content='Learn to count to 10 with stars!',
                culture='Middle Eastern',
                style='visual',
                difficulty_level=1,
                interactive_elements=json.dumps(['counting_game']),
                rewards=json.dumps({'points': 50}),
                learning_objectives=json.dumps(['Count to 10']),
                estimated_time=15
            )
            db.session.add(lesson)
            db.session.commit()
            self.assertEqual(Lesson.query.count(), 1)
            retrieved_lesson = Lesson.query.first()
            self.assertEqual(retrieved_lesson.title, 'Counting Stars')
            self.assertEqual(retrieved_lesson.subject, 'Math')
            self.assertEqual(retrieved_lesson.age_group, '4-6')
            self.assertEqual(retrieved_lesson.content, 'Learn to count to 10 with stars!')
            self.assertEqual(retrieved_lesson.culture, 'Middle Eastern')
            self.assertEqual(retrieved_lesson.style, 'visual')
            self.assertEqual(retrieved_lesson.difficulty_level, 1)
            self.assertEqual(json.loads(retrieved_lesson.interactive_elements), ['counting_game'])
            self.assertEqual(json.loads(retrieved_lesson.rewards), {'points': 50})
            self.assertEqual(json.loads(retrieved_lesson.learning_objectives), ['Count to 10'])
            self.assertEqual(retrieved_lesson.estimated_time, 15)

    def test_emotional_state_creation(self):
        """Test emotional state creation and updates."""
        with self.app.app_context():
            emotion = EmotionalState(user_id=self.user.id, happiness=60, stress_level=20)
            db.session.add(emotion)
            db.session.commit()
            self.assertEqual(EmotionalState.query.count(), 1)
            retrieved_emotion = EmotionalState.query.first()
            self.assertEqual(retrieved_emotion.user_id, self.user.id)
            self.assertEqual(retrieved_emotion.happiness, 60)
            self.assertEqual(retrieved_emotion.stress_level, 20)
            # Test mood update
            retrieved_emotion.add_mood_entry({'mood': 'happy', 'intensity': 1})
            db.session.commit()
            moods = json.loads(retrieved_emotion.recent_moods)
            self.assertEqual(len(moods), 1)
            self.assertEqual(moods[0]['mood'], 'happy')
            self.assertEqual(retrieved_emotion.happiness, 70)  # Increased by 10

    def test_game_progress_creation(self):
        """Test game progress creation and updates."""
        with self.app.app_context():
            game_progress = GameProgress(user_id=self.user.id, game_type='MathQuiz')
            db.session.add(game_progress)
            db.session.commit()
            self.assertEqual(GameProgress.query.count(), 1)
            retrieved_progress = GameProgress.query.first()
            self.assertEqual(retrieved_progress.user_id, self.user.id)
            self.assertEqual(retrieved_progress.game_type, 'MathQuiz')
            self.assertEqual(retrieved_progress.level, 1)
            self.assertEqual(retrieved_progress.score, 0)
            # Test progress update
            retrieved_progress.update_progress(score=100, time_spent=5, success=True)
            db.session.commit()
            self.assertEqual(retrieved_progress.score, 100)
            self.assertEqual(retrieved_progress.attempts, 1)
            self.assertEqual(retrieved_progress.success_rate, 1.0)

    def test_achievement_creation(self):
        """Test achievement creation and user association."""
        with self.app.app_context():
            achievement = Achievement(
                name='First Lesson',
                description='Complete your first lesson!',
                category='learning',
                points_required=50,
                icon='🎓'
            )
            db.session.add(achievement)
            db.session.commit()
            self.assertEqual(Achievement.query.count(), 1)
            retrieved_achievement = Achievement.query.first()
            self.assertEqual(retrieved_achievement.name, 'First Lesson')
            self.assertEqual(retrieved_achievement.points_required, 50)
            # Test user achievement
            self.user.total_points = 60
            db.session.commit()
            self.assertTrue(retrieved_achievement.check_requirements({'total_points': 60}))

    def test_pet_accessory_creation(self):
        """Test pet accessory creation and unlocking."""
        with self.app.app_context():
            accessory = PetAccessory(
                name='Star Hat',
                category='Hat',
                description='A shiny star hat for your pet!',
                unlock_requirement='Level 2'
            )
            db.session.add(accessory)
            db.session.commit()
            self.assertEqual(PetAccessory.query.count(), 1)
            retrieved_accessory = PetAccessory.query.first()
            self.assertEqual(retrieved_accessory.name, 'Star Hat')
            self.assertEqual(retrieved_accessory.category, 'Hat')
            self.assertEqual(retrieved_accessory.unlock_requirement, 'Level 2')

    def test_story_creation(self):
        """Test story creation and publishing."""
        with self.app.app_context():
            story = Story(
                title='The Magic Forest',
                content='A child found a magic tree...',
                genre='adventure',
                creator_id=self.user.id,
                is_collaborative=True
            )
            db.session.add(story)
            db.session.commit()
            self.assertEqual(Story.query.count(), 1)
            retrieved_story = Story.query.first()
            self.assertEqual(retrieved_story.title, 'The Magic Forest')
            self.assertEqual(retrieved_story.content, 'A child found a magic tree...')
            self.assertEqual(retrieved_story.genre, 'adventure')
            self.assertEqual(retrieved_story.creator_id, self.user.id)
            self.assertTrue(retrieved_story.is_collaborative)

    def test_helper_functions(self):
        """Test utility helper functions."""
        self.assertTrue(is_valid_email('testkid@example.com'))
        self.assertFalse(is_valid_email('invalid-email'))
        self.assertTrue(is_valid_password('Test1234'))
        self.assertFalse(is_valid_password('weak'))
        self.assertEqual(generate_child_friendly_message('happy'), '🎉 Yay! You\'re so happy! Let\'s keep the fun going!')
        self.assertEqual(generate_child_friendly_message('invalid'), '🌟 Let\'s have some fun together!')

    def test_user_update(self):
        """Test updating user attributes."""
        with self.app.app_context():
            user = User.query.filter_by(username='testkid').first()
            user.age = 9
            user.preferred_language = 'ar'
            db.session.commit()
            updated_user = User.query.filter_by(username='testkid').first()
            self.assertEqual(updated_user.age, 9)
            self.assertEqual(updated_user.preferred_language, 'ar')

if __name__ == '__main__':
    unittest.main()