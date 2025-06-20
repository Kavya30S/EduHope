// Service Worker Registration and Main App Logic
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}

// Initialize Socket.IO for real-time features
const socket = io();

// Global app state
const AppState = {
    currentUser: null,
    petStatus: {
        happiness: 100,
        hunger: 50,
        energy: 80,
        level: 1,
        experience: 0
    },
    unlockedAccessories: [],
    currentTheme: 'fantasy'
};

// Magical particle system for enhanced UI
class ParticleSystem {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.colors = ['#FF6B9D', '#C44569', '#F8B500', '#6C5CE7', '#A8E6CF'];
        this.init();
    }

    init() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.createParticles();
        this.animate();
    }

    createParticles() {
        for (let i = 0; i < 50; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 2,
                vy: (Math.random() - 0.5) * 2,
                radius: Math.random() * 3 + 1,
                color: this.colors[Math.floor(Math.random() * this.colors.length)],
                alpha: Math.random() * 0.5 + 0.2
            });
        }
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.particles.forEach(particle => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            if (particle.x < 0 || particle.x > this.canvas.width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > this.canvas.height) particle.vy *= -1;
            
            this.ctx.save();
            this.ctx.globalAlpha = particle.alpha;
            this.ctx.fillStyle = particle.color;
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.restore();
        });
        
        requestAnimationFrame(() => this.animate());
    }
}

// Enhanced Learning Progress Tracker
class LearningTracker {
    constructor() {
        this.sessions = JSON.parse(localStorage.getItem('learningSessions')) || [];
        this.streakCount = parseInt(localStorage.getItem('streakCount')) || 0;
        this.lastLoginDate = localStorage.getItem('lastLoginDate');
        this.updateStreak();
    }

    updateStreak() {
        const today = new Date().toDateString();
        if (this.lastLoginDate !== today) {
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            
            if (this.lastLoginDate === yesterday.toDateString()) {
                this.streakCount++;
            } else {
                this.streakCount = 1;
            }
            
            localStorage.setItem('streakCount', this.streakCount);
            localStorage.setItem('lastLoginDate', today);
        }
    }

    addSession(subject, duration, score) {
        const session = {
            subject,
            duration,
            score,
            timestamp: new Date().toISOString(),
            petReward: this.calculatePetReward(score)
        };
        
        this.sessions.push(session);
        localStorage.setItem('learningSessions', JSON.stringify(this.sessions));
        this.updatePetStatus(session.petReward);
    }

    calculatePetReward(score) {
        return {
            happiness: Math.floor(score / 10),
            experience: score * 2,
            food: score > 80 ? 1 : 0
        };
    }

    updatePetStatus(reward) {
        AppState.petStatus.happiness = Math.min(100, AppState.petStatus.happiness + reward.happiness);
        AppState.petStatus.experience += reward.experience;
        
        // Level up logic
        const expNeeded = AppState.petStatus.level * 100;
        if (AppState.petStatus.experience >= expNeeded) {
            AppState.petStatus.level++;
            AppState.petStatus.experience -= expNeeded;
            this.showLevelUpAnimation();
        }
        
        this.savePetStatus();
    }

    showLevelUpAnimation() {
        const modal = document.createElement('div');
        modal.className = 'level-up-modal magical-popup';
        modal.innerHTML = `
            <div class="level-up-content">
                <h2>🎉 Level Up! 🎉</h2>
                <p>Your pet is now Level ${AppState.petStatus.level}!</p>
                <p>New accessories unlocked!</p>
                <button onclick="this.parentElement.parentElement.remove()">Continue</button>
            </div>
        `;
        document.body.appendChild(modal);
    }

    savePetStatus() {
        localStorage.setItem('petStatus', JSON.stringify(AppState.petStatus));
    }
}

// Enhanced Emotion Detection and Support
class EmotionSupport {
    constructor() {
        this.emotions = ['happy', 'sad', 'angry', 'excited', 'worried', 'calm'];
        this.supportMessages = {
            sad: [
                "It's okay to feel sad sometimes. Remember, you're amazing! 🌟",
                "Your pet friend is here to cheer you up! 🐾",
                "Let's do something fun together to brighten your day! ✨"
            ],
            angry: [
                "Take a deep breath with me. In... and out... 🌸",
                "Your pet wants to help you feel better. Let's play! 🎮",
                "Remember, it's okay to feel angry. Let's find a calm activity. 🕯️"
            ],
            worried: [
                "You're braver than you know! Your pet believes in you! 💪",
                "Let's focus on something positive together. 🌈",
                "Take it one step at a time. You've got this! 🌟"
            ]
        };
    }

    async detectEmotion(text) {
        try {
            const response = await fetch('/api/emotion/detect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            return await response.json();
        } catch (error) {
            console.error('Emotion detection error:', error);
            return { emotion: 'neutral', confidence: 0.5 };
        }
    }

    showSupport(emotion) {
        if (this.supportMessages[emotion]) {
            const messages = this.supportMessages[emotion];
            const message = messages[Math.floor(Math.random() * messages.length)];
            this.showSupportModal(message);
        }
    }

    showSupportModal(message) {
        const modal = document.createElement('div');
        modal.className = 'support-modal magical-popup';
        modal.innerHTML = `
            <div class="support-content">
                <div class="pet-avatar bouncing"></div>
                <p>${message}</p>
                <div class="support-actions">
                    <button onclick="this.closest('.support-modal').remove()">Thank you!</button>
                    <button onclick="this.closest('.support-modal').remove(); showBreathingExercise()">Breathing Exercise</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
}

// Breathing Exercise Feature
function showBreathingExercise() {
    const modal = document.createElement('div');
    modal.className = 'breathing-modal magical-popup';
    modal.innerHTML = `
        <div class="breathing-content">
            <h3>Let's Breathe Together 🌸</h3>
            <div class="breathing-circle" id="breathingCircle"></div>
            <p id="breathingText">Get ready...</p>
            <button onclick="startBreathing()" id="startBtn">Start</button>
            <button onclick="this.closest('.breathing-modal').remove()" id="closeBtn" style="display:none;">Close</button>
        </div>
    `;
    document.body.appendChild(modal);
}

function startBreathing() {
    const circle = document.getElementById('breathingCircle');
    const text = document.getElementById('breathingText');
    const startBtn = document.getElementById('startBtn');
    const closeBtn = document.getElementById('closeBtn');
    
    startBtn.style.display = 'none';
    closeBtn.style.display = 'block';
    
    let cycle = 0;
    const maxCycles = 5;
    
    function breatheCycle() {
        if (cycle >= maxCycles) {
            text.textContent = "Great job! You're feeling calmer now. 🌟";
            return;
        }
        
        // Inhale
        text.textContent = "Breathe in... 🌸";
        circle.style.transform = 'scale(1.5)';
        circle.style.backgroundColor = '#A8E6CF';
        
        setTimeout(() => {
            // Hold
            text.textContent = "Hold... ⏸️";
            circle.style.backgroundColor = '#6C5CE7';
        }, 4000);
        
        setTimeout(() => {
            // Exhale
            text.textContent = "Breathe out... 🍃";
            circle.style.transform = 'scale(1)';
            circle.style.backgroundColor = '#FF6B9D';
        }, 6000);
        
        setTimeout(() => {
            cycle++;
            breatheCycle();
        }, 10000);
    }
    
    breatheCycle();
}

// Enhanced Audio System
class AudioManager {
    constructor() {
        this.sounds = {};
        this.musicVolume = 0.3;
        this.sfxVolume = 0.5;
        this.loadSounds();
    }

    loadSounds() {
        const soundFiles = {
            click: '/static/audio/click.mp3',
            achievement: '/static/audio/achievement.mp3',
            levelUp: '/static/audio/levelup.mp3',
            petHappy: '/static/audio/pet-happy.mp3',
            petSad: '/static/audio/pet-sad.mp3',
            backgroundMusic: '/static/audio/background.mp3'
        };

        Object.entries(soundFiles).forEach(([name, url]) => {
            this.sounds[name] = new Audio(url);
            this.sounds[name].volume = name === 'backgroundMusic' ? this.musicVolume : this.sfxVolume;
        });
    }

    play(soundName) {
        if (this.sounds[soundName]) {
            this.sounds[soundName].currentTime = 0;
            this.sounds[soundName].play().catch(e => console.log('Audio play failed:', e));
        }
    }

    playBackgroundMusic() {
        if (this.sounds.backgroundMusic) {
            this.sounds.backgroundMusic.loop = true;
            this.sounds.backgroundMusic.play().catch(e => console.log('Background music failed:', e));
        }
    }

    stopBackgroundMusic() {
        if (this.sounds.backgroundMusic) {
            this.sounds.backgroundMusic.pause();
        }
    }
}

// Initialize systems when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize particle system
    const canvas = document.getElementById('particleCanvas');
    if (canvas) {
        new ParticleSystem(canvas);
    }

    // Initialize learning tracker
    window.learningTracker = new LearningTracker();
    
    // Initialize emotion support
    window.emotionSupport = new EmotionSupport();
    
    // Initialize audio manager
    window.audioManager = new AudioManager();
    
    // Load saved pet status
    const savedPetStatus = localStorage.getItem('petStatus');
    if (savedPetStatus) {
        AppState.petStatus = JSON.parse(savedPetStatus);
    }

    // Update UI with current state
    updatePetStatusDisplay();
    updateStreakDisplay();
    
    // Add click sounds to all buttons
    document.querySelectorAll('button, .btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (window.audioManager) {
                window.audioManager.play('click');
            }
        });
    });

    // Socket.IO event listeners
    socket.on('connect', function() {
        console.log('Connected to server');
    });

    socket.on('pet_update', function(data) {
        AppState.petStatus = data;
        updatePetStatusDisplay();
    });

    socket.on('achievement_unlocked', function(data) {
        showAchievementModal(data);
    });
});

// UI Update Functions
function updatePetStatusDisplay() {
    const elements = {
        happiness: document.getElementById('petHappiness'),
        hunger: document.getElementById('petHunger'),
        energy: document.getElementById('petEnergy'),
        level: document.getElementById('petLevel'),
        experience: document.getElementById('petExperience')
    };

    Object.entries(elements).forEach(([key, element]) => {
        if (element) {
            if (key === 'level') {
                element.textContent = AppState.petStatus[key];
            } else {
                element.style.width = `${AppState.petStatus[key]}%`;
                element.setAttribute('data-value', AppState.petStatus[key]);
            }
        }
    });
}

function updateStreakDisplay() {
    const streakElement = document.getElementById('streakCount');
    if (streakElement && window.learningTracker) {
        streakElement.textContent = window.learningTracker.streakCount;
    }
}

function showAchievementModal(achievement) {
    if (window.audioManager) {
        window.audioManager.play('achievement');
    }
    
    const modal = document.createElement('div');
    modal.className = 'achievement-modal magical-popup';
    modal.innerHTML = `
        <div class="achievement-content">
            <h2>🏆 Achievement Unlocked! 🏆</h2>
            <div class="achievement-icon">${achievement.icon}</div>
            <h3>${achievement.name}</h3>
            <p>${achievement.description}</p>
            <div class="achievement-rewards">
                <p>Rewards: ${achievement.rewards}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()">Awesome!</button>
        </div>
    `;
    document.body.appendChild(modal);
}

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Export functions for global use
window.AppState = AppState;
window.showNotification = showNotification;
window.showBreathingExercise = showBreathingExercise;
window.startBreathing = startBreathing;