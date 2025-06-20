// Enhanced Pet Interaction System
class PetCompanion {
    constructor(petData) {
        this.pet = petData || this.getDefaultPet();
        this.animations = {};
        this.accessories = JSON.parse(localStorage.getItem('petAccessories')) || [];
        this.interactionCooldown = false;
        this.moodSystem = new PetMoodSystem();
        this.initializePet();
        this.startStatusUpdates();
    }

    getDefaultPet() {
        return {
            id: 1,
            name: 'Buddy',
            type: 'dragon',
            level: 1,
            experience: 0,
            happiness: 100,
            hunger: 50,
            energy: 80,
            health: 100,
            last_fed: Date.now(),
            last_played: Date.now(),
            personality: 'friendly',
            color: '#FF6B9D',
            accessories: [],
            skills: {
                flying: 1,
                magic: 1,
                friendship: 1
            },
            achievements: []
        };
    }

    initializePet() {
        this.createPetCanvas();
        this.setupEventListeners();
        this.loadPetAssets();
        this.updatePetDisplay();
        this.startAnimationLoop();
    }

    createPetCanvas() {
        const petContainer = document.getElementById('petContainer');
        if (!petContainer) return;

        const canvas = document.createElement('canvas');
        canvas.id = 'petCanvas';
        canvas.width = 400;
        canvas.height = 400;
        canvas.style.borderRadius = '20px';
        canvas.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        
        petContainer.appendChild(canvas);
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
    }

    loadPetAssets() {
        this.petSprites = {};
        const petTypes = ['dragon', 'unicorn', 'phoenix', 'griffin', 'fairy', 'robot', 'crystal', 'shadow', 'rainbow', 'star'];
        
        petTypes.forEach(type => {
            this.petSprites[type] = {
                idle: new Image(),
                happy: new Image(),
                sad: new Image(),
                eating: new Image(),
                sleeping: new Image(),
                playing: new Image()
            };
            
            Object.keys(this.petSprites[type]).forEach(state => {
                this.petSprites[type][state].src = `/static/images/pets/${type}_${state}.png`;
                this.petSprites[type][state].onerror = () => {
                    // Fallback to emoji-based rendering
                    this.useEmojiRendering = true;
                };
            });
        });
    }

    startAnimationLoop() {
        const animate = () => {
            this.drawPet();
            this.updateParticles();
            requestAnimationFrame(animate);
        };
        animate();
    }

    drawPet() {
        if (!this.ctx) return;
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw background elements
        this.drawEnvironment();
        
        if (this.useEmojiRendering) {
            this.drawEmojiPet();
        } else {
            this.drawSpritePet();
        }
        
        // Draw accessories
        this.drawAccessories();
        
        // Draw status effects
        this.drawStatusEffects();
        
        // Draw interaction feedback
        this.drawInteractionFeedback();
    }

    drawEmojiPet() {
        const petEmojis = {
            dragon: '🐉',
            unicorn: '🦄',
            phoenix: '🔥',
            griffin: '🦅',
            fairy: '🧚',
            robot: '🤖',
            crystal: '💎',
            shadow: '👻',
            rainbow: '🌈',
            star: '⭐'
        };
        
        const emoji = petEmojis[this.pet.type] || '🐉';
        const size = 100 + (this.pet.level * 5);
        
        // Add floating animation
        const floatOffset = Math.sin(Date.now() * 0.003) * 10;
        
        this.ctx.font = `${size}px Arial`;
        this.ctx.textAlign = 'center';
        this.ctx.fillText(emoji, this.canvas.width / 2, this.canvas.height / 2 + floatOffset);
        
        // Draw pet name
        this.ctx.font = '24px Arial';
        this.ctx.fillStyle = '#fff';
        this.ctx.fillText(this.pet.name, this.canvas.width / 2, this.canvas.height - 50);
    }

    drawSpritePet() {
        const currentState = this.getCurrentPetState();
        const sprite = this.petSprites[this.pet.type][currentState];
        
        if (sprite && sprite.complete) {
            const size = 150 + (this.pet.level * 10);
            const x = (this.canvas.width - size) / 2;
            const y = (this.canvas.height - size) / 2;
            
            // Add floating animation
            const floatOffset = Math.sin(Date.now() * 0.003) * 10;
            
            this.ctx.drawImage(sprite, x, y + floatOffset, size, size);
        }
    }

    drawEnvironment() {
        // Draw magical environment based on pet type
        const gradients = {
            dragon: ['#FF6B6B', '#4ECDC4'],
            unicorn: ['#FF9A9E', '#FECFEF'],
            phoenix: ['#FA709A', '#FEE140'],
            fairy: ['#A8EDEA', '#FED6E3'],
            robot: ['#667eea', '#764ba2'],
            default: ['#667eea', '#764ba2']
        };
        
        const colors = gradients[this.pet.type] || gradients.default;
        const gradient = this.ctx.createLinearGradient(0, 0, 0, this.canvas.height);
        gradient.addColorStop(0, colors[0]);
        gradient.addColorStop(1, colors[1]);
        
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Add sparkles
        this.drawSparkles();
    }

    drawSparkles() {
        const sparkleCount = 20;
        const time = Date.now() * 0.001;
        
        for (let i = 0; i < sparkleCount; i++) {
            const x = (Math.sin(time + i) * 0.5 + 0.5) * this.canvas.width;
            const y = (Math.cos(time * 0.7 + i) * 0.5 + 0.5) * this.canvas.height;
            const alpha = (Math.sin(time * 2 + i) * 0.5 + 0.5) * 0.8;
            
            this.ctx.save();
            this.ctx.globalAlpha = alpha;
            this.ctx.fillStyle = '#fff';
            this.ctx.font = '16px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('✨', x, y);
            this.ctx.restore();
        }
    }

    drawAccessories() {
        this.accessories.forEach(accessory => {
            // Draw accessory on pet based on type
            this.ctx.save();
            this.ctx.globalAlpha = 0.9;
            this.ctx.font = '40px Arial';
            this.ctx.textAlign = 'center';
            
            const positions = {
                hat: { x: this.canvas.width / 2, y: this.canvas.height / 2 - 80 },
                collar: { x: this.canvas.width / 2, y: this.canvas.height / 2 + 20 },
                wings: { x: this.canvas.width / 2 - 50, y: this.canvas.height / 2 }
            };
            
            const pos = positions[accessory.type] || positions.collar;
            this.ctx.fillText(accessory.emoji, pos.x, pos.y);
            this.ctx.restore();
        });
    }

    drawStatusEffects() {
        const effects = [];
        
        if (this.pet.happiness > 80) effects.push({ emoji: '😊', text: 'Happy' });
        if (this.pet.hunger < 20) effects.push({ emoji: '😴', text: 'Hungry' });
        if (this.pet.energy < 30) effects.push({ emoji: '💤', text: 'Sleepy' });
        if (this.pet.level > 5) effects.push({ emoji: '⭐', text: 'Experienced' });
        
        effects.forEach((effect, index) => {
            const x = 50;
            const y = 50 + (index * 30);
            
            this.ctx.save();
            this.ctx.font = '20px Arial';
            this.ctx.fillStyle = '#fff';
            this.ctx.shadowColor = '#000';
            this.ctx.shadowBlur = 3;
            this.ctx.fillText(`${effect.emoji} ${effect.text}`, x, y);
            this.ctx.restore();
        });
    }

    drawInteractionFeedback() {
        if (this.lastInteraction) {
            const timeSince = Date.now() - this.lastInteraction.timestamp;
            if (timeSince < 2000) {
                const alpha = 1 - (timeSince / 2000);
                
                this.ctx.save();
                this.ctx.globalAlpha = alpha;
                this.ctx.font = '24px Arial';
                this.ctx.fillStyle = this.lastInteraction.color;
                this.ctx.textAlign = 'center';
                this.ctx.fillText(
                    this.lastInteraction.text,
                    this.canvas.width / 2,
                    this.canvas.height / 2 - 100
                );
                this.ctx.restore();
            }
        }
    }

    getCurrentPetState() {
        if (this.pet.energy < 20) return 'sleeping';
        if (this.pet.hunger < 30) return 'sad';
        if (this.pet.happiness > 80) return 'happy';
        if (this.isEating) return 'eating';
        if (this.isPlaying) return 'playing';
        return 'idle';
    }

    setupEventListeners() {
        // Pet interaction buttons
        const feedBtn = document.getElementById('feedPet');
        const playBtn = document.getElementById('playWithPet');
        const petBtn = document.getElementById('petPet');
        const teachBtn = document.getElementById('teachPet');

        if (feedBtn) feedBtn.addEventListener('click', () => this.feedPet());
        if (playBtn) playBtn.addEventListener('click', () => this.playWithPet());
        if (petBtn) petBtn.addEventListener('click', () => this.petPet());
        if (teachBtn) teachBtn.addEventListener('click', () => this.teachPet());

        // Canvas click for direct interaction
        if (this.canvas) {
            this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
        }

        // Pet customization
        document.querySelectorAll('.pet-color-option').forEach(btn => {
            btn.addEventListener('click', (e) => this.changePetColor(e.target.dataset.color));
        });

        // Accessory buttons
        document.querySelectorAll('.accessory-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.toggleAccessory(e.target.dataset.accessory));
        });
    }

    handleCanvasClick(event) {
        if (this.interactionCooldown) return;

        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Check if click is on pet
        const petCenterX = this.canvas.width / 2;
        const petCenterY = this.canvas.height / 2;
        const distance = Math.sqrt((x - petCenterX) ** 2 + (y - petCenterY) ** 2);

        if (distance < 100) {
            this.petPet();
        }
    }

    async feedPet() {
        if (this.interactionCooldown) return;
        
        this.interactionCooldown = true;
        this.isEating = true;
        
        const food = this.selectRandomFood();
        const hungerIncrease = food.value;
        const happinessIncrease = Math.floor(hungerIncrease / 2);

        this.pet.hunger = Math.min(100, this.pet.hunger + hungerIncrease);
        this.pet.happiness = Math.min(100, this.pet.happiness + happinessIncrease);
        this.pet.last_fed = Date.now();

        this.showInteractionFeedback(`+${hungerIncrease} Hunger! ${food.emoji}`, '#4ECDC4');
        
        if (window.audioManager) {
            window.audioManager.play('petHappy');
        }

        // Animation duration
        setTimeout(() => {
            this.isEating = false;
            this.interactionCooldown = false;
        }, 2000);

        await this.savePetData();
        this.updatePetDisplay();
        this.checkAchievements();
    }

    async playWithPet() {
        if (this.interactionCooldown) return;
        
        this.interactionCooldown = true;
        this.isPlaying = true;

        const game = this.selectRandomGame();
        const energyDecrease = game.energyCost;
        const happinessIncrease = game.happiness;
        const experienceGain = game.experience;

        this.pet.energy = Math.max(0, this.pet.energy - energyDecrease);
        this.pet.happiness = Math.min(100, this.pet.happiness + happinessIncrease);
        this.pet.experience += experienceGain;
        this.pet.last_played = Date.now();

        this.showInteractionFeedback(`+${experienceGain} XP! ${game.emoji}`, '#FF6B9D');
        
        if (window.audioManager) {
            window.audioManager.play('petHappy');
        }

        this.checkLevelUp();

        setTimeout(() => {
            this.isPlaying = false;
            this.interactionCooldown = false;
        }, 3000);

        await this.savePetData();
        this.updatePetDisplay();
        this.checkAchievements();
    }

    async petPet() {
        if (this.interactionCooldown) return;
        
        this.interactionCooldown = true;

        const affectionGain = 5 + Math.floor(Math.random() * 10);
        this.pet.happiness = Math.min(100, this.pet.happiness + affectionGain);

        const responses = [
            { text: "Purr... 😸", color: '#FF9A9E' },
            { text: "So cozy! 🥰", color: '#FECFEF' },
            { text: "*Happy sounds* 😊", color: '#A8EDEA' },
            { text: "More pets! 🐾", color: '#FED6E3' }
        ];

        const response = responses[Math.floor(Math.random() * responses.length)];
        this.showInteractionFeedback(response.text, response.color);

        if (window.audioManager) {
            window.audioManager.play('petHappy');
        }

        setTimeout(() => {
            this.interactionCooldown = false;
        }, 1000);

        await this.savePetData();
        this.updatePetDisplay();
    }

    async teachPet() {
        if (this.interactionCooldown) return;
        
        this.interactionCooldown = true;

        const skill = this.selectRandomSkill();
        const skillIncrease = 1;
        const experienceGain = 20;

        this.pet.skills[skill.name] = (this.pet.skills[skill.name] || 0) + skillIncrease;
        this.pet.experience += experienceGain;

        this.showInteractionFeedback(`${skill.emoji} +1 ${skill.displayName}!`, '#6C5CE7');
        
        if (window.audioManager) {
            window.audioManager.play('achievement');
        }

        this.checkLevelUp();

        setTimeout(() => {
            this.interactionCooldown = false;
        }, 2000);

        await this.savePetData();
        this.updatePetDisplay();
        this.checkAchievements();
    }

    selectRandomFood() {
        const foods = [
            { name: 'Magic Berry', emoji: '🫐', value: 25 },
            { name: 'Crystal Apple', emoji: '🍎', value: 20 },
            { name: 'Rainbow Cake', emoji: '🎂', value: 30 },
            { name: 'Star Fruit', emoji: '⭐', value: 35 },
            { name: 'Moon Cookie', emoji: '🍪', value: 15 }
        ];
        return foods[Math.floor(Math.random() * foods.length)];
    }

    selectRandomGame() {
        const games = [
            { name: 'Flying Race', emoji: '🏃‍♂️', energyCost: 15, happiness: 20, experience: 15 },
            { name: 'Treasure Hunt', emoji: '🗺️', energyCost: 20, happiness: 25, experience: 20 },
            { name: 'Magic Practice', emoji: '✨', energyCost: 10, happiness: 15, experience: 25 },
            { name: 'Dance Party', emoji: '💃', energyCost: 12, happiness: 30, experience: 10 },
            { name: 'Puzzle Solving', emoji: '🧩', energyCost: 8, happiness: 18, experience: 30 }
        ];
        return games[Math.floor(Math.random() * games.length)];
    }

    selectRandomSkill() {
        const skills = [
            { name: 'flying', displayName: 'Flying', emoji: '🪶' },
            { name: 'magic', displayName: 'Magic', emoji: '✨' },
            { name: 'friendship', displayName: 'Friendship', emoji: '💖' },
            { name: 'wisdom', displayName: 'Wisdom', emoji: '🧠' },
            { name: 'courage', displayName: 'Courage', emoji: '🦁' }
        ];
        return skills[Math.floor(Math.random() * skills.length)];
    }

    showInteractionFeedback(text, color) {
        this.lastInteraction = {
            text: text,
            color: color,
            timestamp: Date.now()
        };
    }

    checkLevelUp() {
        const expNeeded = this.pet.level * 100;
        if (this.pet.experience >= expNeeded) {
            this.pet.level++;
            this.pet.experience -= expNeeded;
            this.showLevelUpAnimation();
            this.unlockRandomAccessory();
        }
    }

    showLevelUpAnimation() {
        if (window.audioManager) {
            window.audioManager.play('levelUp');
        }

        const modal = document.createElement('div');
        modal.className = 'level-up-modal magical-popup';
        modal.innerHTML = `
            <div class="level-up-content">
                <h2>🎉 Level Up! 🎉</h2>
                <p>${this.pet.name} is now Level ${this.pet.level}!</p>
                <div class="level-up-stats">
                    <p>✨ New abilities unlocked!</p>
                    <p>🎁 Random accessory unlocked!</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="magical-btn">
                    Amazing! ⭐
                </button>
            </div>
        `;
        document.body.appendChild(modal);
    }

    unlockRandomAccessory() {
        const accessories = [
            { type: 'hat', name: 'Wizard Hat', emoji: '🎩', cost: 0 },
            { type: 'collar', name: 'Magic Collar', emoji: '💎', cost: 0 },
            { type: 'wings', name: 'Rainbow Wings', emoji: '🌈', cost: 0 },
            { type: 'crown', name: 'Royal Crown', emoji: '👑', cost: 0 },
            { type: 'bowtie', name: 'Fancy Bowtie', emoji: '🎀', cost: 0 }
        ];

        const unlockedAccessories = this.accessories.map(a => a.type);
        const availableAccessories = accessories.filter(a => !unlockedAccessories.includes(a.type));

        if (availableAccessories.length > 0) {
            const newAccessory = availableAccessories[Math.floor(Math.random() * availableAccessories.length)];
            this.accessories.push(newAccessory);
            localStorage.setItem('petAccessories', JSON.stringify(this.accessories));
            
            showNotification(`🎁 Unlocked: ${newAccessory.name} ${newAccessory.emoji}`, 'success');
        }
    }

    changePetColor(color) {
        this.pet.color = color;
        this.savePetData();
        showNotification('Pet color changed! 🎨', 'info');
    }

    toggleAccessory(accessoryType) {
        const accessoryIndex = this.pet.accessories.indexOf(accessoryType);
        
        if (accessoryIndex > -1) {
            this.pet.accessories.splice(accessoryIndex, 1);
        } else {
            const accessory = this.accessories.find(a => a.type === accessoryType);
            if (accessory) {
                this.pet.accessories.push(accessoryType);
            }
        }
        
        this.savePetData();
        this.updatePetDisplay();
    }

    checkAchievements() {
        const achievements = [
            { id: 'first_feed', name: 'First Meal', condition: () => this.pet.last_fed > 0 },
            { id: 'level_5', name: 'Growing Strong', condition: () => this.pet.level >= 5 },
            { id: 'max_happiness', name: 'Pure Joy', condition: () => this.pet.happiness === 100 },
            { id: 'skill_master', name: 'Skill Master', condition: () => Object.values(this.pet.skills).some(s => s >= 10) }
        ];

        achievements.forEach(achievement => {
            if (!this.pet.achievements.includes(achievement.id) && achievement.condition()) {
                this.pet.achievements.push(achievement.id);
                this.showAchievementUnlocked(achievement);
            }
        });
    }

    showAchievementUnlocked(achievement) {
        if (window.showAchievementModal) {
            window.showAchievementModal({
                name: achievement.name,
                icon: '🏆',
                description: 'You and your pet accomplished something amazing!',
                rewards: 'Special bond points ❤️'
            });
        }
    }

    startStatusUpdates() {
        setInterval(() => {
            this.updatePetNeeds();
        }, 60000); // Update every minute
    }

    updatePetNeeds() {
        const now = Date.now();
        const timeSinceLastFeed = now - this.pet.last_fed;
        const timeSinceLastPlay = now - this.pet.last_played;

        // Gradual hunger increase
        if (timeSinceLastFeed > 1800000) { // 30 minutes
            this.pet.hunger = Math.max(0, this.pet.hunger - 1);
        }

        // Gradual happiness decrease if not played with
        if (timeSinceLastPlay > 3600000) { // 1 hour
            this.pet.happiness = Math.max(0, this.pet.happiness - 1);
        }

        // Energy regeneration during rest
        if (this.pet.energy < 100 && !this.isPlaying) {
            this.pet.energy = Math.min(100, this.pet.energy + 1);
        }

        this.savePetData();
        this.updatePetDisplay();
    }

    updatePetDisplay() {
        // Update status bars
        const statusBars = {
            happiness: document.getElementById('petHappiness'),
            hunger: document.getElementById('petHunger'),
            energy: document.getElementById('petEnergy')
        };

        Object.entries(statusBars).forEach(([stat, element]) => {
            if (element) {
                element.style.width = `${this.pet[stat]}%`;
                element.setAttribute('data-value', this.pet[stat]);
                
                // Color coding for status bars
                if (this.pet[stat] < 30) {
                    element.style.backgroundColor = '#FF6B6B';
                } else if (this.pet[stat] < 60) {
                    element.style.backgroundColor = '#FFE66D';
                } else {
                    element.style.backgroundColor = '#4ECDC4';
                }
            }
        });

        // Update level and experience
        const levelElement = document.getElementById('petLevel');
        const expElement = document.getElementById('petExperience');
        
        if (levelElement) levelElement.textContent = this.pet.level;
        if (expElement) {
            const expNeeded = this.pet.level * 100;
            const expPercent = (this.pet.experience / expNeeded) * 100;
            expElement.style.width = `${expPercent}%`;
        }

        // Update pet name
        const nameElement = document.getElementById('petName');
        if (nameElement) nameElement.textContent = this.pet.name;
    }

    async savePetData() {
        try {
            await fetch('/api/pet/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.pet)
            });
            
            // Also save locally for offline use
            localStorage.setItem('petData', JSON.stringify(this.pet));
        } catch (error) {
            console.error('Failed to save pet data:', error);
            // Save locally as fallback
            localStorage.setItem('petData', JSON.stringify(this.pet));
        }
    }
}

// Pet Mood System for more realistic behavior
class PetMoodSystem {
    constructor() {
        this.moods = ['happy', 'playful', 'sleepy', 'hungry', 'excited', 'calm'];
        this.currentMood = 'happy';
        this.moodTimer = 0;
        this.moodDuration = 300000; // 5 minutes per mood
    }

    updateMood(pet) {
        this.moodTimer += 1000;
        
        if (this.moodTimer >= this.moodDuration) {
            this.currentMood = this.calculateNewMood(pet);
            this.moodTimer = 0;
        }
        
        return this.currentMood;
    }

    calculateNewMood(pet) {
        if (pet.hunger < 30) return 'hungry';
        if (pet.energy < 30) return 'sleepy';
        if (pet.happiness > 80) return 'happy';
        if (pet.happiness > 60) return 'playful';
        return 'calm';
    }
}

// Initialize pet system when page loads
document.addEventListener('DOMContentLoaded', function() {
    const petContainer = document.getElementById('petContainer');
    if (petContainer) {
        // Load saved pet data or create new pet
        const savedPetData = localStorage.getItem('petData');
        const petData = savedPetData ? JSON.parse(savedPetData) : null;
        
        window.petCompanion = new PetCompanion(petData);
    }
});

// Export for global use
window.PetCompanion = PetCompanion;