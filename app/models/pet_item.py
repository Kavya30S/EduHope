from app import db
from datetime import datetime

class PetItem(db.Model):
    __tablename__ = 'pet_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    item_type = db.Column(db.String(50), nullable=False)  # food, toy, accessory, medicine
    cost = db.Column(db.Integer, nullable=False, default=0)
    
    # Effects when used
    happiness_effect = db.Column(db.Integer, default=0)
    health_effect = db.Column(db.Integer, default=0)
    energy_effect = db.Column(db.Integer, default=0)
    hunger_effect = db.Column(db.Integer, default=0)
    
    # Item properties
    consumable = db.Column(db.Boolean, default=True)  # Whether item is consumed when used
    available = db.Column(db.Boolean, default=True)
    rarity = db.Column(db.String(20), default='common')  # common, rare, epic, legendary
    icon = db.Column(db.String(10), default='🎁')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PetItem {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'item_type': self.item_type,
            'cost': self.cost,
            'happiness_effect': self.happiness_effect,
            'health_effect': self.health_effect,
            'energy_effect': self.energy_effect,
            'hunger_effect': self.hunger_effect,
            'consumable': self.consumable,
            'rarity': self.rarity,
            'icon': self.icon
        }
    
    @staticmethod
    def create_default_items():
        """Create default pet items"""
        default_items = [
            # Food items
            {
                'name': 'Basic Pet Food',
                'description': 'Standard nutritious food for your pet',
                'item_type': 'food',
                'cost': 5,
                'hunger_effect': 20,
                'happiness_effect': 5,
                'icon': '🥘',
                'rarity': 'common'
            },
            {
                'name': 'Premium Pet Food',
                'description': 'High-quality food that pets love',
                'item_type': 'food',
                'cost': 15,
                'hunger_effect': 40,
                'happiness_effect': 10,
                'icon': '🍖',
                'rarity': 'rare'
            },
            {
                'name': 'Deluxe Feast',
                'description': 'A special meal fit for a pet king!',
                'item_type': 'food',
                'cost': 25,
                'hunger_effect': 60,
                'happiness_effect': 20,
                'health_effect': 10,
                'icon': '🍗',
                'rarity': 'epic'
            },
            
            # Toys
            {
                'name': 'Rubber Ball',
                'description': 'A classic toy that never gets old',
                'item_type': 'toy',
                'cost': 10,
                'happiness_effect': 15,
                'energy_effect': -5,
                'consumable': False,
                'icon': '⚽',
                'rarity': 'common'
            },
            {
                'name': 'Squeaky Toy',
                'description': 'Makes fun sounds that pets love',
                'item_type': 'toy',
                'cost': 20,
                'happiness_effect': 25,
                'energy_effect': -10,
                'consumable': False,
                'icon': '🧸',
                'rarity': 'rare'
            },
            {
                'name': 'Interactive Puzzle',
                'description': 'Challenges your pet mentally',
                'item_type': 'toy',
                'cost': 35,
                'happiness_effect': 30,
                'energy_effect': -15,
                'consumable': False,
                'icon': '🧩',
                'rarity': 'epic'
            },
            
            # Medicine
            {
                'name': 'Health Potion',
                'description': 'Restores your pet\'s health',
                'item_type': 'medicine',
                'cost': 20,
                'health_effect': 50,
                'happiness_effect': 5,
                'icon': '💉',
                'rarity': 'common'
            },
            {
                'name': 'Energy Boost',
                'description': 'Gives your pet a burst of energy',
                'item_type': 'medicine',
                'cost': 15,
                'energy_effect': 40,
                'happiness_effect': 10,
                'icon': '⚡',
                'rarity': 'common'
            },
            {
                'name': 'Happiness Pill',
                'description': 'Instantly cheers up your pet',
                'item_type': 'medicine',
                'cost': 18,
                'happiness_effect': 35,
                'health_effect': 5,
                'icon': '💊',
                'rarity': 'rare'
            },
            
            # Accessories
            {
                'name': 'Cute Collar',
                'description': 'A stylish collar for your pet',
                'item_type': 'accessory',
                'cost': 30,
                'happiness_effect': 20,
                'consumable': False,
                'icon': '🦴',
                'rarity': 'rare'
            },
            {
                'name': 'Golden Crown',
                'description': 'Makes your pet feel like royalty',
                'item_type': 'accessory',
                'cost': 100,
                'happiness_effect': 50,
                'health_effect': 20,
                'consumable': False,
                'icon': '👑',
                'rarity': 'legendary'
            },
            {
                'name': 'Magic Wings',
                'description': 'Gives your pet the power of flight',
                'item_type': 'accessory',
                'cost': 75,
                'happiness_effect': 40,
                'energy_effect': 30,
                'consumable': False,
                'icon': '🪶',
                'rarity': 'epic'
            }
        ]
        
        for item_data in default_items:
            existing = PetItem.query.filter_by(name=item_data['name']).first()
            if not existing:
                item = PetItem(**item_data)
                db.session.add(item)
        
        db.session.commit()