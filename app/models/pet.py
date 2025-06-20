from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    pet_type = db.Column(db.String(50), nullable=False)
    
    # Pet stats
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    happiness = db.Column(db.Integer, default=50)
    hunger = db.Column(db.Integer, default=50)
    energy = db.Column(db.Integer, default=100)
    health = db.Column(db.Integer, default=100)
    
    # Progression
    unlocked_accessories = db.Column(db.Text, default='[]')  # JSON array
    unlocked_toys = db.Column(db.Text, default='[]')  # JSON array
    personality_traits = db.Column(db.Text, default='[]')  # JSON array
    
    # Timestamps
    last_fed = db.Column(db.DateTime, default=datetime.utcnow)
    last_played = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('pets', lazy=True))
    
    @staticmethod
    def get_available_pets():
        """Return list of 20+ fantasy pet types with descriptions"""
        return [
            {
                'type': 'fire_dragon',
                'name': 'Fire Dragon',
                'description': 'A majestic dragon that breathes colorful flames and loves adventure!',
                'personality': ['brave', 'energetic', 'protective'],
                'color': '#FF6B35',
                'unlock_requirement': 0
            },
            {
                'type': 'ice_phoenix',
                'name': 'Ice Phoenix',
                'description': 'A beautiful phoenix with crystal wings that sparkles like snow!',
                'personality': ['elegant', 'wise', 'calm'],
                'color': '#87CEEB',
                'unlock_requirement': 0
            },
            {
                'type': 'rainbow_unicorn',
                'name': 'Rainbow Unicorn',
                'description': 'A magical unicorn with a rainbow mane that grants wishes!',
                'personality': ['magical', 'kind', 'joyful'],
                'color': '#FF69B4',
                'unlock_requirement': 0
            },
            {
                'type': 'space_fox',
                'name': 'Space Fox',
                'description': 'A clever fox from the stars with glowing fur and cosmic powers!',
                'personality': ['clever', 'curious', 'playful'],
                'color': '#9370DB',
                'unlock_requirement': 50
            },
            {
                'type': 'crystal_wolf',
                'name': 'Crystal Wolf',
                'description': 'A loyal wolf made of shimmering crystals that howls melodies!',
                'personality': ['loyal', 'strong', 'musical'],
                'color': '#40E0D0',
                'unlock_requirement': 100
            },
            {
                'type': 'cloud_leopard',
                'name': 'Cloud Leopard',
                'description': 'A swift leopard that can walk on clouds and control weather!',
                'personality': ['swift', 'mysterious', 'free'],
                'color': '#F0F8FF',
                'unlock_requirement': 150
            },
            {
                'type': 'dream_butterfly',
                'name': 'Dream Butterfly',
                'description': 'A giant butterfly that carries dreams and spreads happiness!',
                'personality': ['gentle', 'dreamy', 'inspiring'],
                'color': '#FFB6C1',
                'unlock_requirement': 200
            },
            {
                'type': 'thunder_tiger',
                'name': 'Thunder Tiger',
                'description': 'A powerful tiger with lightning stripes and booming roar!',
                'personality': ['powerful', 'bold', 'electric'],
                'color': '#FFD700',
                'unlock_requirement': 250
            },
            {
                'type': 'forest_sprite',
                'name': 'Forest Sprite',
                'description': 'A tiny magical being that makes flowers bloom wherever it goes!',
                'personality': ['tiny', 'magical', 'nature-loving'],
                'color': '#90EE90',
                'unlock_requirement': 300
            },
            {
                'type': 'ocean_seahorse',
                'name': 'Ocean Seahorse',
                'description': 'A majestic seahorse that rides ocean waves and speaks with dolphins!',
                'personality': ['graceful', 'wise', 'peaceful'],
                'color': '#20B2AA',
                'unlock_requirement': 350
            },
            {
                'type': 'star_rabbit',
                'name': 'Star Rabbit',
                'description': 'A fluffy rabbit with star-shaped spots that hops between dimensions!',
                'personality': ['cute', 'bouncy', 'dimensional'],
                'color': '#DDA0DD',
                'unlock_requirement': 400
            },
            {
                'type': 'shadow_panther',
                'name': 'Shadow Panther',
                'description': 'A sleek panther that can blend with shadows and move silently!',
                'personality': ['stealthy', 'mysterious', 'agile'],
                'color': '#2F4F4F',
                'unlock_requirement': 450
            },
            {
                'type': 'wind_eagle',
                'name': 'Wind Eagle',
                'description': 'A magnificent eagle that soars through storms and commands the wind!',
                'personality': ['majestic', 'free', 'storm-loving'],
                'color': '#4682B4',
                'unlock_requirement': 500
            },
            {
                'type': 'lava_salamander',
                'name': 'Lava Salamander',
                'description': 'A friendly salamander that swims in lava and creates precious gems!',
                'personality': ['friendly', 'hot-tempered', 'creative'],
                'color': '#FF4500',
                'unlock_requirement': 550
            },
            {
                'type': 'moon_owl',
                'name': 'Moon Owl',
                'description': 'A wise owl with silver feathers that glows under moonlight!',
                'personality': ['wise', 'nocturnal', 'mystical'],
                'color': '#C0C0C0',
                'unlock_requirement': 600
            },
            {
                'type': 'cosmic_cat',
                'name': 'Cosmic Cat',
                'description': 'A playful cat with galaxy patterns that can travel through space!',
                'personality': ['playful', 'cosmic', 'curious'],
                'color': '#483D8B',
                'unlock_requirement': 650
            },
            {
                'type': 'flower_deer',
                'name': 'Flower Deer',
                'description': 'A gentle deer with antlers made of blooming flowers!',
                'personality': ['gentle', 'nature-loving', 'peaceful'],
                'color': '#F0E68C',
                'unlock_requirement': 700
            },
            {
                'type': 'aurora_bear',
                'name': 'Aurora Bear',
                'description': 'A cuddly bear that creates northern lights with its fur!',
                'personality': ['cuddly', 'magical', 'colorful'],
                'color': '#00FF7F',
                'unlock_requirement': 750
            },
            {
                'type': 'prism_snake',
                'name': 'Prism Snake',
                'description': 'A beautiful snake that reflects rainbows and speaks in colors!',
                'personality': ['colorful', 'hypnotic', 'artistic'],
                'color': '#FF1493',
                'unlock_requirement': 800
            },
            {
                'type': 'time_turtle',
                'name': 'Time Turtle',
                'description': 'An ancient turtle that can slow down or speed up time!',
                'personality': ['ancient', 'wise', 'temporal'],
                'color': '#8B4513',
                'unlock_requirement': 850
            },
            {
                'type': 'void_hamster',
                'name': 'Void Hamster',
                'description': 'A tiny hamster that controls dark matter and stores infinite snacks!',
                'personality': ['tiny', 'powerful', 'snack-loving'],
                'color': '#191970',
                'unlock_requirement': 900
            },
            {
                'type': 'quantum_ferret',
                'name': 'Quantum Ferret',
                'description': 'A playful ferret that exists in multiple dimensions simultaneously!',
                'personality': ['playful', 'quantum', 'multi-dimensional'],
                'color': '#FF6347',
                'unlock_requirement': 950
            },
            {
                'type': 'legendary_phoenix',
                'name': 'Legendary Phoenix',
                'description': 'The ultimate phoenix that grants eternal wisdom and rebirth!',
                'personality': ['legendary', 'wise', 'eternal'],
                'color': '#DC143C',
                'unlock_requirement': 1000
            }
        ]
    
    def get_unlocked_accessories(self):
        """Get list of unlocked accessories"""
        try:
            return json.loads(self.unlocked_accessories)
        except:
            return []
    
    def add_accessory(self, accessory_name):
        """Add new accessory to pet"""
        accessories = self.get_unlocked_accessories()
        if accessory_name not in accessories:
            accessories.append(accessory_name)
            self.unlocked_accessories = json.dumps(accessories)
    
    def get_unlocked_toys(self):
        """Get list of unlocked toys"""
        try:
            return json.loads(self.unlocked_toys)
        except:
            return []
    
    def add_toy(self, toy_name):
        """Add new toy to pet"""
        toys = self.get_unlocked_toys()
        if toy_name not in toys:
            toys.append(toy_name)
            self.unlocked_toys = json.dumps(toys)
    
    def get_personality_traits(self):
        """Get personality traits"""
        try:
            return json.loads(self.personality_traits)
        except:
            return []
    
    def feed(self, food_type='regular'):
        """Feed the pet and update stats"""
        food_effects = {
            'regular': {'hunger': -30, 'happiness': 10, 'experience': 5},
            'premium': {'hunger': -50, 'happiness': 20, 'experience': 10},
            'magical': {'hunger': -40, 'happiness': 30, 'experience': 15, 'energy': 20}
        }
        
        effects = food_effects.get(food_type, food_effects['regular'])
        
        self.hunger = max(0, min(100, self.hunger + effects['hunger']))
        self.happiness = max(0, min(100, self.happiness + effects['happiness']))
        self.experience += effects['experience']
        
        if 'energy' in effects:
            self.energy = max(0, min(100, self.energy + effects['energy']))
        
        self.last_fed = datetime.utcnow()
        self.check_level_up()
    
    def play(self, activity='basic'):
        """Play with pet and update stats"""
        play_effects = {
            'basic': {'happiness': 15, 'energy': -10, 'experience': 8},
            'training': {'happiness': 10, 'energy': -20, 'experience': 15},
            'adventure': {'happiness': 25, 'energy': -15, 'experience': 20}
        }
        
        effects = play_effects.get(activity, play_effects['basic'])
        
        if self.energy >= abs(effects['energy']):
            self.happiness = max(0, min(100, self.happiness + effects['happiness']))
            self.energy = max(0, min(100, self.energy + effects['energy']))
            self.experience += effects['experience']
            self.last_played = datetime.utcnow()
            self.check_level_up()
            return True
        return False
    
    def check_level_up(self):
        """Check if pet should level up"""
        required_exp = self.level * 100
        if self.experience >= required_exp:
            self.level += 1
            self.experience -= required_exp
            self.health = 100  # Restore health on level up
            
            # Unlock new accessories/toys based on level
            self.unlock_level_rewards()
    
    def unlock_level_rewards(self):
        """Unlock rewards based on level"""
        level_rewards = {
            2: {'accessory': 'Sparkly Collar', 'toy': 'Rainbow Ball'},
            3: {'accessory': 'Magic Hat', 'toy': 'Glowing Stick'},
            5: {'accessory': 'Wings of Wonder', 'toy': 'Puzzle Cube'},
            7: {'accessory': 'Crown of Wisdom', 'toy': 'Melody Box'},
            10: {'accessory': 'Armor of Courage', 'toy': 'Time Crystal'},
            15: {'accessory': 'Cape of Heroes', 'toy': 'Dream Catcher'},
            20: {'accessory': 'Legendary Aura', 'toy': 'Infinity Stone'}
        }
        
        if self.level in level_rewards:
            reward = level_rewards[self.level]
            if 'accessory' in reward:
                self.add_accessory(reward['accessory'])
            if 'toy' in reward:
                self.add_toy(reward['toy'])
    
    def get_mood(self):
        """Get pet's current mood based on stats"""
        avg_stat = (self.happiness + self.energy + (100 - self.hunger) + self.health) / 4
        
        if avg_stat >= 80:
            return {'mood': 'Ecstatic', 'emoji': '🌟', 'message': f'{self.name} is absolutely glowing with joy!'}
        elif avg_stat >= 60:
            return {'mood': 'Happy', 'emoji': '😊', 'message': f'{self.name} is feeling great!'}
        elif avg_stat >= 40:
            return {'mood': 'Content', 'emoji': '😌', 'message': f'{self.name} is doing okay.'}
        elif avg_stat >= 20:
            return {'mood': 'Sad', 'emoji': '😢', 'message': f'{self.name} needs some attention.'}
        else:
            return {'mood': 'Very Sad', 'emoji': '😭', 'message': f'{self.name} really needs your care!'}
    
    def get_status(self):
        """Get comprehensive pet status"""
        return {
            'name': self.name,
            'type': self.pet_type,
            'level': self.level,
            'experience': self.experience,
            'happiness': self.happiness,
            'hunger': self.hunger,
            'energy': self.energy,
            'health': self.health,
            'mood': self.get_mood(),
            'accessories': self.get_unlocked_accessories(),
            'toys': self.get_unlocked_toys(),
            'traits': self.get_personality_traits()
        }
    
    def to_dict(self):
        """Convert pet to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'pet_type': self.pet_type,
            'level': self.level,
            'experience': self.experience,
            'happiness': self.happiness,
            'hunger': self.hunger,
            'energy': self.energy,
            'health': self.health,
            'unlocked_accessories': self.get_unlocked_accessories(),
            'unlocked_toys': self.get_unlocked_toys(),
            'personality_traits': self.get_personality_traits(),
            'mood': self.get_mood(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }