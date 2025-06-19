from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random

db = SQLAlchemy()

class Pet(db.Model):
    __tablename__ = 'pets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    pet_type = db.Column(db.String(20), nullable=False)  # dragon, unicorn, robot, phoenix, cat
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    happiness = db.Column(db.Integer, default=100)  # 0-100
    hunger = db.Column(db.Integer, default=50)      # 0-100 (100 = very hungry)
    energy = db.Column(db.Integer, default=100)     # 0-100
    health = db.Column(db.Integer, default=100)     # 0-100
    
    # Special attributes
    friendship_level = db.Column(db.Integer, default=1)
    mood = db.Column(db.String(20), default='happy')
    favorite_subject = db.Column(db.String(20))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_fed = db.Column(db.DateTime)
    last_played = db.Column(db.DateTime)
    last_update = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Customization
    color = db.Column(db.String(20), default='default')
    accessories = db.Column(db.Text)  # JSON string of accessories
    
    def __repr__(self):
        return f'<Pet {self.name} ({self.pet_type})>'
    
    def get_experience_to_next_level(self):
        """Calculate experience needed for next level"""
        return self.level * 100
    
    def add_experience(self, exp):
        """Add experience and handle level ups"""
        self.experience += exp
        leveled_up = False
        
        while self.experience >= self.get_experience_to_next_level():
            self.experience -= self.get_experience_to_next_level()
            self.level += 1
            leveled_up = True
            
            # Bonus stats on level up
            self.happiness = min(100, self.happiness + 10)
            self.health = min(100, self.health + 5)
        
        return leveled_up
    
    def feed(self, food_quality=1):
        """Feed the pet - reduces hunger, increases happiness"""
        hunger_reduction = 20 * food_quality
        happiness_boost = 10 * food_quality
        
        self.hunger = max(0, self.hunger - hunger_reduction)
        self.happiness = min(100, self.happiness + happiness_boost)
        self.last_fed = datetime.utcnow()
        
        # Add experience for feeding
        exp_gained = 5 * food_quality
        return self.add_experience(exp_gained)
    
    def play(self, activity_type='normal'):
        """Play with pet - increases happiness, decreases energy"""
        if self.energy < 10:
            return False, "Pet is too tired to play!"
        
        energy_cost = 15
        happiness_boost = 20
        
        if activity_type == 'educational':
            energy_cost = 10
            happiness_boost = 25
        elif activity_type == 'adventure':
            energy_cost = 25
            happiness_boost = 30
        
        self.energy = max(0, self.energy - energy_cost)
        self.happiness = min(100, self.happiness + happiness_boost)
        self.last_played = datetime.utcnow()
        
        # Add experience for playing
        exp_gained = 10 if activity_type == 'educational' else 8
        leveled_up = self.add_experience(exp_gained)
        
        return True, f"Had fun playing! {'Leveled up!' if leveled_up else ''}"
    
    def rest(self):
        """Rest the pet - restores energy"""
        self.energy = min(100, self.energy + 30)
        self.happiness = min(100, self.happiness + 5)
    
    def update_status(self):
        """Update pet status based on time passed"""
        now = datetime.utcnow()
        
        # Calculate time since last update
        if self.last_update:
            time_diff = now - self.last_update
            hours_passed = time_diff.total_seconds() / 3600
        else:
            hours_passed = 0
            self.last_update = now
        
        if hours_passed > 0:
            # Gradual hunger increase
            hunger_increase = min(5 * hours_passed, 30)
            self.hunger = min(100, self.hunger + hunger_increase)
            
            # Gradual energy recovery
            energy_recovery = min(3 * hours_passed, 20)
            self.energy = min(100, self.energy + energy_recovery)
            
            # Happiness decreases if hungry or bored
            if self.hunger > 80:
                self.happiness = max(0, self.happiness - 10)
            elif hours_passed > 24:  # If not played with for a day
                self.happiness = max(0, self.happiness - 5)
            
            self.last_update = now
        
        # Update mood based on stats
        self.update_mood()
    
    def update_mood(self):
        """Update pet mood based on current stats"""
        if self.happiness > 80 and self.hunger < 30:
            self.mood = 'ecstatic'
        elif self.happiness > 60 and self.hunger < 50:
            self.mood = 'happy'
        elif self.happiness > 40:
            self.mood = 'content'
        elif self.happiness > 20:
            self.mood = 'sad'
        else:
            self.mood = 'depressed'
        
        if self.hunger > 80:
            self.mood = 'hungry'
        if self.energy < 20:
            self.mood = 'tired'
    
    def get_status_message(self):
        """Get a status message based on pet's current state"""
        messages = {
            'ecstatic': f"{self.name} is absolutely thrilled to see you! ✨",
            'happy': f"{self.name} is cheerful and ready for adventures! 😊",
            'content': f"{self.name} is doing well and enjoying life! 😌",
            'sad': f"{self.name} seems a bit down. Maybe some playtime would help? 😢",
            'depressed': f"{self.name} is feeling very sad. Show some love! 💔",
            'hungry': f"{self.name} is really hungry! Time for a meal! 🍎",
            'tired': f"{self.name} is tired and needs some rest. 😴"
        }
        
        return messages.get(self.mood, f"{self.name} is doing okay.")
    
    def get_random_interaction(self):
        """Get a random interaction based on pet type"""
        interactions = {
            'dragon': [
                f"{self.name} breathes a small puff of colorful smoke! 🐲",
                f"{self.name} shows off by doing a little flip in the air! ✨",
                f"{self.name} finds a shiny math problem to solve! 📚"
            ],
            'unicorn': [
                f"{self.name} creates a beautiful rainbow! 🌈",
                f"{self.name} prances gracefully around you! 🦄",
                f"{self.name} helps you learn new words with magic! ✨"
            ],
            'robot': [
                f"{self.name} beeps happily and shows cool calculations! 🤖",
                f"{self.name} projects holographic learning materials! 📱",
                f"{self.name} scans for interesting science facts! 🔬"
            ],
            'phoenix': [
                f"{self.name} glows with warm, inspiring light! 🔥",
                f"{self.name} shares an ancient story of wisdom! 📜",
                f"{self.name} encourages you to be creative! 🎨"
            ],
            'cat': [
                f"{self.name} purrs contentedly and rubs against you! 🐱",
                f"{self.name} playfully chases a ball of yarn! 🧶",
                f"{self.name} finds a cozy spot for a quick nap! 💤"
            ]
        }
        
        pet_interactions = interactions.get(self.pet_type, [f"{self.name} is happy to see you!"])
        return random.choice(pet_interactions)
    
    def get_care_tip(self):
        """Get a care tip based on current pet status"""
        if self.hunger > 70:
            return "Your pet is getting hungry! Complete a lesson or game to earn points for food."
        elif self.happiness < 40:
            return "Your pet seems sad. Try playing together or completing educational activities!"
        elif self.energy < 30:
            return "Your pet is tired. Let them rest or do some calm educational activities."
        else:
            return "Your pet is doing great! Keep up the good work with learning activities!"
    
    def to_dict(self):
        """Convert pet to dictionary for JSON responses"""
        return {
            'id': self.id,
            'name': self.name,
            'pet_type': self.pet_type,
            'level': self.level,
            'experience': self.experience,
            'experience_to_next_level': self.get_experience_to_next_level(),
            'happiness': self.happiness,
            'hunger': self.hunger,
            'energy': self.energy,
            'health': self.health,
            'friendship_level': self.friendship_level,
            'mood': self.mood,
            'color': self.color,
            'status_message': self.get_status_message(),
            'care_tip': self.get_care_tip(),
            'random_interaction': self.get_random_interaction()
        }