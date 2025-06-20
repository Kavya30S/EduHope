"""
Pet Accessory Model for managing pet accessories and unlockables
"""
from app import db
from datetime import datetime
import json

class PetAccessory(db.Model):
    __tablename__ = 'pet_accessories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'hat', 'clothing', 'toy', 'background', 'special'
    description = db.Column(db.Text)
    unlock_requirement = db.Column(db.String(100))  # 'level_5', 'score_1000', 'streak_10', etc.
    rarity = db.Column(db.String(20), default='common')  # 'common', 'rare', 'epic', 'legendary'
    image_url = db.Column(db.String(200))
    animation_data = db.Column(db.Text)  # JSON for animation properties
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, category, **kwargs):
        self.name = name
        self.category = category
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_animation_data(self):
        """Parse and return animation data as dictionary"""
        if self.animation_data:
            try:
                return json.loads(self.animation_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_animation_data(self, data):
        """Set animation data as JSON string"""
        self.animation_data = json.dumps(data)

    def check_unlock_requirement(self, user_progress):
        """Check if user meets unlock requirement"""
        if not self.unlock_requirement:
            return True
            
        req_parts = self.unlock_requirement.split('_')
        req_type = req_parts[0]
        req_value = int(req_parts[1]) if len(req_parts) > 1 else 0
        
        if req_type == 'level':
            return max([p.level for p in user_progress], default=0) >= req_value
        elif req_type == 'score':
            return max([p.highest_score for p in user_progress], default=0) >= req_value
        elif req_type == 'streak':
            return max([p.streak_count for p in user_progress], default=0) >= req_value
        elif req_type == 'time':
            return sum([p.time_spent for p in user_progress]) >= req_value
            
        return False

    def to_dict(self, unlocked=False):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'unlock_requirement': self.unlock_requirement,
            'rarity': self.rarity,
            'image_url': self.image_url,
            'animation_data': self.get_animation_data(),
            'unlocked': unlocked,
            'is_active': self.is_active
        }

    @staticmethod
    def get_default_accessories():
        """Get default accessories that should be available to all users"""
        return PetAccessory.query.filter_by(unlock_requirement=None, is_active=True).all()

    @staticmethod
    def get_unlockable_accessories():
        """Get accessories that require unlocking"""
        return PetAccessory.query.filter(
            PetAccessory.unlock_requirement.isnot(None),
            PetAccessory.is_active == True
        ).all()

    def __repr__(self):
        return f'<PetAccessory {self.name} ({self.category})>'


class UserPetAccessory(db.Model):
    __tablename__ = 'user_pet_accessories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    accessory_id = db.Column(db.Integer, db.ForeignKey('pet_accessories.id'), nullable=False)
    is_equipped = db.Column(db.Boolean, default=False)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='pet_accessories')
    pet = db.relationship('Pet', backref='accessories')
    accessory = db.relationship('PetAccessory', backref='user_accessories')

    # Unique constraint to prevent duplicate accessories per user-pet combination
    __table_args__ = (
        db.UniqueConstraint('user_id', 'pet_id', 'accessory_id', name='unique_user_pet_accessory'),
    )

    def __init__(self, user_id, pet_id, accessory_id, **kwargs):
        self.user_id = user_id
        self.pet_id = pet_id
        self.accessory_id = accessory_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def equip(self):
        """Equip this accessory (unequip others in same category)"""
        # Unequip other accessories in the same category for this pet
        same_category_accessories = UserPetAccessory.query.join(PetAccessory).filter(
            UserPetAccessory.user_id == self.user_id,
            UserPetAccessory.pet_id == self.pet_id,
            PetAccessory.category == self.accessory.category,
            UserPetAccessory.id != self.id
        ).all()
        
        for acc in same_category_accessories:
            acc.is_equipped = False
            
        self.is_equipped = True
        db.session.commit()

    def unequip(self):
        """Unequip this accessory"""
        self.is_equipped = False
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'pet_id': self.pet_id,
            'accessory': self.accessory.to_dict(unlocked=True),
            'is_equipped': self.is_equipped,
            'unlocked_at': self.unlocked_at.isoformat() if self.unlocked_at else None
        }

    @staticmethod
    def get_user_accessories(user_id, pet_id=None):
        """Get all accessories owned by user, optionally filtered by pet"""
        query = UserPetAccessory.query.filter_by(user_id=user_id)
        if pet_id:
            query = query.filter_by(pet_id=pet_id)
        return query.all()

    @staticmethod
    def get_equipped_accessories(user_id, pet_id):
        """Get all equipped accessories for a specific pet"""
        return UserPetAccessory.query.filter_by(
            user_id=user_id,
            pet_id=pet_id,
            is_equipped=True
        ).all()

    @staticmethod
    def unlock_accessory(user_id, pet_id, accessory_id):
        """Unlock an accessory for a user's pet"""
        existing = UserPetAccessory.query.filter_by(
            user_id=user_id,
            pet_id=pet_id,
            accessory_id=accessory_id
        ).first()
        
        if existing:
            return existing
            
        new_accessory = UserPetAccessory(
            user_id=user_id,
            pet_id=pet_id,
            accessory_id=accessory_id
        )
        db.session.add(new_accessory)
        db.session.commit()
        return new_accessory

    def __repr__(self):
        return f'<UserPetAccessory {self.user_id}:{self.pet_id}:{self.accessory_id}>'