"""
Fantasy Pet Service - Magical companion system with 20+ fantasy pets
"""
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.models.pet import Pet
from app.models.pet_accessory import PetAccessory
from app.models.user import User
from app import db

class FantasyPetService:
    """Service for managing fantasy pets and their magical interactions"""
    
    # 20+ Fantasy Pets with magical personalities
    FANTASY_PETS = {
        'dragon': {
            'name': 'Sparkle Dragon',
            'type': 'dragon',
            'rarity': 'legendary',
            'base_stats': {'health': 100, 'happiness': 80, 'energy': 90, 'magic': 95},
            'personality': 'brave_loyal',
            'special_ability': 'fire_breath',
            'unlock_requirement': 0,
            'description': '🐲 A majestic dragon with shimmering scales who loves adventures!',
            'care_needs': ['dragon_gems', 'flame_fruits', 'sky_adventures']
        },
        'unicorn': {
            'name': 'Rainbow Unicorn',
            'type': 'unicorn',
            'rarity': 'legendary',
            'base_stats': {'health': 95, 'happiness': 100, 'energy': 85, 'magic': 100},
            'personality': 'gentle_magical',
            'special_ability': 'rainbow_healing',
            'unlock_requirement': 0,
            'description': '🦄 A beautiful unicorn who spreads joy and magic everywhere!',
            'care_needs': ['rainbow_flowers', 'crystal_water', 'moonlight_walks']
        },
        'phoenix': {
            'name': 'Flame Phoenix',
            'type': 'phoenix',
            'rarity': 'legendary',
            'base_stats': {'health': 90, 'happiness': 85, 'energy': 100, 'magic': 90},
            'personality': 'wise_mystical',
            'special_ability': 'rebirth_healing',
            'unlock_requirement': 500,
            'description': '🔥🐦 A magnificent phoenix that rises from ashes with eternal wisdom!',
            'care_needs': ['flame_seeds', 'golden_nectar', 'sunset_meditation']
        },
        'fairy_cat': {
            'name': 'Glitter Fairy Cat',
            'type': 'fairy_cat',
            'rarity': 'epic',
            'base_stats': {'health': 80, 'happiness': 95, 'energy': 90, 'magic': 85},
            'personality': 'playful_mischievous',
            'special_ability': 'pixie_dust',
            'unlock_requirement': 200,
            'description': '🐱✨ A magical cat with fairy wings who loves to play pranks!',
            'care_needs': ['fairy_treats', 'butterfly_milk', 'flower_naps']
        },
        'crystal_wolf': {
            'name': 'Aurora Wolf',
            'type': 'crystal_wolf',
            'rarity': 'epic',
            'base_stats': {'health': 85, 'happiness': 75, 'energy': 95, 'magic': 80},
            'personality': 'loyal_mysterious',
            'special_ability': 'crystal_howl',
            'unlock_requirement': 300,
            'description': '🐺💎 A mystical wolf with crystal fur that glows under moonlight!',
            'care_needs': ['moon_berries', 'crystal_springs', 'forest_runs']
        },
        'space_bunny': {
            'name': 'Cosmic Bunny',
            'type': 'space_bunny',
            'rarity': 'rare',
            'base_stats': {'health': 70, 'happiness': 90, 'energy': 80, 'magic': 75},
            'personality': 'curious_adventurous',
            'special_ability': 'star_jump',
            'unlock_requirement': 150,
            'description': '🐰🌟 An adorable bunny from outer space who hops on star trails!',
            'care_needs': ['star_carrots', 'cosmic_milk', 'meteor_games']
        },
        'rainbow_fox': {
            'name': 'Prism Fox',
            'type': 'rainbow_fox',
            'rarity': 'rare',
            'base_stats': {'health': 75, 'happiness': 85, 'energy': 90, 'magic': 80},
            'personality': 'clever_colorful',
            'special_ability': 'color_change',
            'unlock_requirement': 100,
            'description': '🦊🌈 A clever fox whose fur changes colors with emotions!',
            'care_needs': ['rainbow_berries', 'prism_water', 'color_puzzles']
        },
        'baby_griffon': {
            'name': 'Fluffy Griffon',
            'type': 'baby_griffon',
            'rarity': 'epic',
            'base_stats': {'health': 80, 'happiness': 80, 'energy': 85, 'magic': 85},
            'personality': 'noble_playful',
            'special_ability': 'wind_soar',
            'unlock_requirement': 250,
            'description': '🦅🦁 A baby griffon with eagle wings and lion heart!',
            'care_needs': ['golden_fish', 'wind_currents', 'cloud_nests']
        },
        'magic_turtle': {
            'name': 'Wisdom Turtle',
            'type': 'magic_turtle',
            'rarity': 'uncommon',
            'base_stats': {'health': 100, 'happiness': 70, 'energy': 60, 'magic': 90},
            'personality': 'wise_patient',
            'special_ability': 'time_slow',
            'unlock_requirement': 80,
            'description': '🐢✨ An ancient turtle who carries the wisdom of ages!',
            'care_needs': ['wisdom_kelp', 'time_bubbles', 'meditation_stones']
        },
        'starlight_deer': {
            'name': 'Celestial Deer',
            'type': 'starlight_deer',
            'rarity': 'rare',
            'base_stats': {'health': 85, 'happiness': 90, 'energy': 80, 'magic': 85},
            'personality': 'gentle_ethereal',
            'special_ability': 'starlight_heal',
            'unlock_requirement': 180,
            'description': '🦌⭐ A graceful deer with antlers that sparkle like stars!',
            'care_needs': ['starfruit', 'moonbeam_grass', 'constellation_dances']
        },
        'cloud_sheep': {
            'name': 'Dreamy Sheep',
            'type': 'cloud_sheep',
            'rarity': 'common',
            'base_stats': {'health': 75, 'happiness': 95, 'energy': 70, 'magic': 60},
            'personality': 'sleepy_dreamy',
            'special_ability': 'dream_weaving',
            'unlock_requirement': 50,
            'description': '🐑☁️ A fluffy sheep made of clouds who creates beautiful dreams!',
            'care_needs': ['dream_flowers', 'cloud_cotton', 'lullaby_winds']
        },
        'fire_salamander': {
            'name': 'Ember Salamander',
            'type': 'fire_salamander',
            'rarity': 'uncommon',
            'base_stats': {'health': 70, 'happiness': 75, 'energy': 95, 'magic': 70},
            'personality': 'energetic_warm',
            'special_ability': 'flame_dash',
            'unlock_requirement': 120,
            'description': '🦎🔥 A small salamander with a warm heart and fiery spirit!',
            'care_needs': ['flame_bugs', 'warm_rocks', 'fire_dances']
        },
        'ice_penguin': {
            'name': 'Frost Penguin',
            'type': 'ice_penguin',
            'rarity': 'uncommon',
            'base_stats': {'health': 80, 'happiness': 85, 'energy': 75, 'magic': 65},
            'personality': 'cool_social',
            'special_ability': 'ice_slide',
            'unlock_requirement': 90,
            'description': '🐧❄️ A cheerful penguin who loves ice adventures and fish!',
            'care_needs': ['ice_fish', 'snow_cones', 'sliding_games']
        },
        'flower_fairy': {
            'name': 'Blossom Fairy',
            'type': 'flower_fairy',
            'rarity': 'rare',
            'base_stats': {'health': 65, 'happiness': 100, 'energy': 80, 'magic': 95},
            'personality': 'cheerful_nurturing',
            'special_ability': 'bloom_magic',
            'unlock_requirement': 160,
            'description': '🧚‍♀️🌸 A tiny fairy who makes flowers bloom with her magical touch!',
            'care_needs': ['pollen_drops', 'flower_nectar', 'garden_songs']
        },
        'shadow_cat': {
            'name': 'Mystic Shadow Cat',
            'type': 'shadow_cat',
            'rarity': 'epic',
            'base_stats': {'health': 75, 'happiness': 70, 'energy': 90, 'magic': 90},
            'personality': 'mysterious_loyal',
            'special_ability': 'shadow_walk',
            'unlock_requirement': 280,
            'description': '🐱‍👤🌙 A mysterious cat who walks through shadows and moonbeams!',
            'care_needs': ['shadow_milk', 'midnight_treats', 'moon_gazing']
        },
        'crystal_dragon': {
            'name': 'Diamond Dragon',
            'type': 'crystal_dragon',
            'rarity': 'legendary',
            'base_stats': {'health': 95, 'happiness': 80, 'energy': 85, 'magic': 100},
            'personality': 'majestic_protective',
            'special_ability': 'crystal_shield',
            'unlock_requirement': 400,
            'description': '🐉💎 A magnificent dragon with scales like precious diamonds!',
            'care_needs': ['crystal_gems', 'diamond_dust', 'treasure_hunts']
        },
        'wind_eagle': {
            'name': 'Storm Eagle',
            'type': 'wind_eagle',
            'rarity': 'epic',
            'base_stats': {'health': 85, 'happiness': 75, 'energy': 100, 'magic': 80},
            'personality': 'free_spirited_brave',
            'special_ability': 'storm_call',
            'unlock_requirement': 320,
            'description': '🦅⚡ A powerful eagle who rides the storm winds!',
            'care_needs': ['storm_seeds', 'wind_currents', 'mountain_flights']
        },
        'magic_hamster': {
            'name': 'Sparkle Hamster',
            'type': 'magic_hamster',
            'rarity': 'common',
            'base_stats': {'health': 60, 'happiness': 95, 'energy': 85, 'magic': 55},
            'personality': 'adorable_energetic',
            'special_ability': 'sparkle_spin',
            'unlock_requirement': 30,
            'description': '🐹✨ The cutest hamster who leaves sparkles wherever it goes!',
            'care_needs': ['magic_seeds', 'sparkle_water', 'wheel_races']
        },
        'lunar_moth': {
            'name': 'Moonbeam Moth',
            'type': 'lunar_moth',
            'rarity': 'rare',
            'base_stats': {'health': 70, 'happiness': 80, 'energy': 75, 'magic': 85},
            'personality': 'serene_mystical',
            'special_ability': 'moon_dust',
            'unlock_requirement': 200,
            'description': '🦋🌙 A beautiful moth that glows with soft moonlight!',
            'care_needs': ['moon_nectar', 'night_flowers', 'lunar_dances']
        },
        'ocean_dolphin': {
            'name': 'Splash Dolphin',
            'type': 'ocean_dolphin',
            'rarity': 'uncommon',
            'base_stats': {'health': 85, 'happiness': 90, 'energy': 80, 'magic': 70},
            'personality': 'playful_intelligent',
            'special_ability': 'water_splash',
            'unlock_requirement': 110,
            'description': '🐬💙 A friendly dolphin who loves to play in the magical waters!',
            'care_needs': ['coral_fish', 'sea_bubbles', 'wave_surfing']
        },
        'golden_monkey': {
            'name': 'Treasure Monkey',
            'type': 'golden_monkey',
            'rarity': 'rare',
            'base_stats': {'health': 80, 'happiness': 85, 'energy': 90, 'magic': 75},
            'personality': 'clever_mischievous',
            'special_ability': 'treasure_find',
            'unlock_requirement': 170,
            'description': '🐵✨ A clever monkey with golden fur who finds hidden treasures!',
            'care_needs': ['golden_bananas', 'treasure_nuts', 'jungle_swings']
        }
    }
    
    # Magical accessories for pets
    PET_ACCESSORIES = {
        'crowns': ['Sparkle Crown', 'Rainbow Crown', 'Crystal Crown', 'Golden Crown'],
        'wings': ['Fairy Wings', 'Dragon Wings', 'Angel Wings', 'Butterfly Wings'],
        'toys': ['Magic Ball', 'Star Wand', 'Crystal Cube', 'Rainbow Ring'],
        'food': ['Magic Treats', 'Star Cookies', 'Crystal Candy', 'Rainbow Cake'],
        'homes': ['Castle Tower', 'Cloud House', 'Crystal Cave', 'Tree House'],
        'clothes': ['Magic Cape', 'Sparkle Vest', 'Rainbow Scarf', 'Crystal Necklace']
    }
    
    @staticmethod
    def get_available_pets(user_points: int) -> List[Dict]:
        """Get pets available based on user points"""
        available_pets = []
        for pet_id, pet_data in FantasyPetService.FANTASY_PETS.items():
            if user_points >= pet_data['unlock_requirement']:
                available_pets.append({
                    'id': pet_id,
                    'data': pet_data,
                    'unlocked': True
                })
            else:
                available_pets.append({
                    'id': pet_id,
                    'data': pet_data,
                    'unlocked': False,
                    'points_needed': pet_data['unlock_requirement'] - user_points
                })
        return available_pets
    
    @staticmethod
    def adopt_pet(user_id: int, pet_type: str) -> Optional[Pet]:
        """Adopt a new fantasy pet"""
        if pet_type not in FantasyPetService.FANTASY_PETS:
            return None
            
        pet_data = FantasyPetService.FANTASY_PETS[pet_type]
        
        # Check if user already has this pet
        existing_pet = Pet.query.filter_by(user_id=user_id, pet_type=pet_type).first()
        if existing_pet:
            return existing_pet
        
        # Create new pet
        new_pet = Pet(
            user_id=user_id,
            name=pet_data['name'],
            pet_type=pet_type,
            level=1,
            experience=0,
            health=pet_data['base_stats']['health'],
            happiness=pet_data['base_stats']['happiness'],
            energy=pet_data['base_stats']['energy'],
            magic_power=pet_data['base_stats']['magic'],
            personality=pet_data['personality'],
            special_ability=pet_data['special_ability'],
            last_interaction=datetime.utcnow()
        )
        
        db.session.add(new_pet)
        db.session.commit()
        return new_pet
    
    @staticmethod
    def feed_pet(pet: Pet, food_type: str) -> Dict:
        """Feed the pet and update stats"""
        feed_effects = {
            'magic_treats': {'health': 10, 'happiness': 15, 'energy': 5},
            'star_cookies': {'health': 5, 'happiness': 20, 'energy': 10},
            'crystal_candy': {'health': 8, 'happiness': 12, 'magic_power': 5},
            'rainbow_cake': {'health': 15, 'happiness': 25, 'energy': 15}
        }
        
        if food_type not in feed_effects:
            return {'success': False, 'message': 'Unknown food type!'}
        
        effects = feed_effects[food_type]
        messages = []
        
        # Apply effects
        for stat, boost in effects.items():
            current_value = getattr(pet, stat)
            new_value = min(current_value + boost, 100)  # Cap at 100
            setattr(pet, stat, new_value)
            messages.append(f"{stat.replace('_', ' ').title()} +{boost}")
        
        # Add experience
        pet.experience += 10
        if pet.experience >= pet.level * 100:
            pet.level += 1
            pet.experience = 0
            messages.append(f"🎉 Level Up! Now Level {pet.level}!")
        
        pet.last_interaction = datetime.utcnow()
        db.session.commit()
        
        return {
            'success': True,
            'message': f"🍽️ {pet.name} enjoyed the {food_type}!",
            'effects': messages,
            'pet_response': FantasyPetService._get_pet_response(pet, 'feed')
        }
    
    @staticmethod
    def play_with_pet(pet: Pet, game_type: str) -> Dict:
        """Play games with the pet"""
        games = {
            'fetch': {'happiness': 20, 'energy': -10, 'experience': 15},
            'hide_seek': {'happiness': 25, 'energy': -15, 'experience': 20},
            'magic_tricks': {'happiness': 15, 'magic_power': 5, 'experience': 25},
            'flying_race': {'happiness': 30, 'energy': -20, 'experience': 30}
        }
        
        if game_type not in games:
            return {'success': False, 'message': 'Unknown game!'}
        
        effects = games[game_type]
        messages = []
        
        # Apply effects
        for stat, change in effects.items():
            if stat == 'experience':
                pet.experience += change
                if pet.experience >= pet.level * 100:
                    pet.level += 1
                    pet.experience = 0
                    messages.append(f"🎉 Level Up! Now Level {pet.level}!")
            else:
                current_value = getattr(pet, stat)
                new_value = max(0, min(current_value + change, 100))
                setattr(pet, stat, new_value)
                if change > 0:
                    messages.append(f"{stat.replace('_', ' ').title()} +{change}")
        
        pet.last_interaction = datetime.utcnow()
        db.session.commit()
        
        return {
            'success': True,
            'message': f"🎮 {pet.name} had fun playing {game_type}!",
            'effects': messages,
            'pet_response': FantasyPetService._get_pet_response(pet, 'play')
        }
    
    @staticmethod
    def pet_interaction(pet: Pet) -> Dict:
        """Simple pet interaction for affection"""
        pet.happiness = min(pet.happiness + 5, 100)
        pet.last_interaction = datetime.utcnow()
        db.session.commit()
        
        return {
            'success': True,
            'message': f"💖 {pet.name} loves your attention!",
            'pet_response': FantasyPetService._get_pet_response(pet, 'pet')
        }
    
    @staticmethod
    def check_pet_needs(pet: Pet) -> Dict:
        """Check if pet needs attention"""
        now = datetime.utcnow()
        time_since_interaction = now - pet.last_interaction
        hours_passed = time_since_interaction.total_seconds() / 3600
        
        # Decrease stats over time
        health_decrease = min(int(hours_passed * 2), pet.health)
        happiness_decrease = min(int(hours_passed * 3), pet.happiness)
        energy_decrease = min(int(hours_passed * 1), pet.energy)
        
        pet.health = max(0, pet.health - health_decrease)
        pet.happiness = max(0, pet.happiness - happiness_decrease)
        pet.energy = max(0, pet.energy - energy_decrease)
        
        needs = []
        if pet.health < 30:
            needs.append('health')
        if pet.happiness < 30:
            needs.append('happiness')
        if pet.energy < 30:
            needs.append('energy')
        
        db.session.commit()
        
        return {
            'needs': needs,
            'pet_mood': FantasyPetService._get_pet_mood(pet),
            'urgent': len(needs) > 2
        }
    
    @staticmethod
    def _get_pet_mood(pet: Pet) -> str:
        """Get pet's current mood based on stats"""
        avg_stat = (pet.health + pet.happiness + pet.energy) / 3
        
        if avg_stat >= 80:
            return 'ecstatic'
        elif avg_stat >= 60:
            return 'happy'
        elif avg_stat >= 40:
            return 'okay'
        elif avg_stat >= 20:
            return 'sad'
        else:
            return 'very_sad'
    
    @staticmethod
    def _get_pet_response(pet: Pet, action: str) -> str:
        """Get pet's response based on personality and action"""
        responses = {
            'brave_loyal': {
                'feed': ["*roars happily* That was delicious!", "*nuzzles gratefully*", "Ready for our next adventure!"],
                'play': ["*breathes happy sparks*", "Let's soar together!", "*does a victory dance*"],
                'pet': ["*purrs like thunder*", "You're my favorite human!", "*tail wags excitedly*"]
            },
            'gentle_magical': {
                'feed': ["*sparkles with joy* Thank you!", "*magical shimmer*", "This tastes like rainbows!"],
                'play': ["*creates rainbow trails*", "Magic is more fun with friends!", "*giggles melodically*"],
                'pet': ["*glows softly*", "Your kindness fills my heart!", "*nuzzles gently*"]
            },
            'playful_mischievous': {
                'feed': ["*pounces on food excitedly*", "Yum yum yum!", "*does a happy dance*"],
                'play': ["*zooms around playfully*", "Again! Again!", "*giggles mischievously*"],
                'pet': ["*purrs and rolls over*", "More pets please!", "*playful meow*"]
            }
        }
        
        personality = pet.personality
        if personality in responses and action in responses[personality]:
            return random.choice(responses[personality][action])
        
        return "*happy pet sounds*"
    
    @staticmethod
    def unlock_accessory(user_id: int, pet_id: int, accessory_type: str, accessory_name: str) -> bool:
        """Unlock accessory for pet"""
        # Check if accessory already exists
        existing = PetAccessory.query.filter_by(
            user_id=user_id, 
            pet_id=pet_id, 
            accessory_name=accessory_name
        ).first()
        
        if existing:
            return False
        
        # Create new accessory
        accessory = PetAccessory(
            user_id=user_id,
            pet_id=pet_id,
            accessory_type=accessory_type,
            accessory_name=accessory_name,
            is_equipped=False
        )
        
        db.session.add(accessory)
        db.session.commit()
        return True
    
    @staticmethod
    def get_pet_status(pet: Pet) -> Dict:
        """Get comprehensive pet status"""
        needs = FantasyPetService.check_pet_needs(pet)
        
        return {
            'pet': {
                'id': pet.id,
                'name': pet.name,
                'type': pet.pet_type,
                'level': pet.level,
                'experience': pet.experience,
                'health': pet.health,
                'happiness': pet.happiness,
                'energy': pet.energy,
                'magic_power': pet.magic_power,
                'mood': needs['pet_mood'],
                'special_ability': pet.special_ability
            },
            'needs': needs['needs'],
            'urgent': needs['urgent'],
            'last_interaction': pet.last_interaction.isoformat(),
            'accessories': [acc.to_dict() for acc in pet.accessories]
        }