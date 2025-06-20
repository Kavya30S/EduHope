// Language Game JavaScript - Real-time AI-powered learning
class LanguageGameEngine {
    constructor() {
        this.socket = io();
        this.currentGame = null;
        this.currentLevel = 1;
        this.score = 0;
        this.streak = 0;
        this.lives = 3;
        this.gameData = {};
        this.isRecording = false;
        this.speechRecognition = null;
        this.currentChallenge = null;
        this.userProgress = {};
        
        this.initializeGame();
        this.setupSocketListeners();
        this.initializeSpeechRecognition();
    }
    
    initializeGame() {
        this.updateScoreDisplay();
        this.loadUserProgress();
        
        // Real-time learning adaptation
        this.socket.emit('get_user_language_profile', {
            user_id: window.userId || 'guest'
        });
    }
    
    setupSocketListeners() {
        // Receive personalized challenges
        this.socket.on('language_challenge', (data) => {
            this.handleNewChallenge(data);
        });
        
        // Receive AI feedback
        this.socket.on('ai_feedback', (data) => {
            this.handleAIFeedback(data);
        });
        
        // Real-time difficulty adjustment
        this.socket.on('difficulty_adjusted', (data) => {
            this.adjustDifficulty(data);
        });
        
        // Pet reactions
        this.socket.on('pet_reaction', (data) => {
            this.showPetReaction(data);
        });
        
        // Progress updates
        this.socket.on('progress_updated', (data) => {
            this.updateProgress(data);
        });
    }
    
    initializeSpeechRecognition() {
        if ('webkitSpeechRecognition' in window) {
            this.speechRecognition = new webkitSpeechRecognition();
            this.speechRecognition.continuous = false;
            this.speechRecognition.interimResults = false;
            this.speechRecognition.lang = 'en-US';
            
            this.speechRecognition.onresult = (event) => {
                const result = event.results[0][0].transcript;
                this.handleSpeechResult(result);
            };
            
            this.speechRecognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.handleSpeechError(event.error);
            };
        }
    }
    
    startGame(gameType) {
        this.currentGame = gameType;
        this.hideAllGameAreas();
        
        // Show selected game area
        document.getElementById(`${gameType}Game`).style.display = 'block';
        document.getElementById('gameModes').style.display = 'none';
        
        // Request AI-generated challenge
        this.socket.emit('request_language_challenge', {
            game_type: gameType,
            user_level: this.currentLevel,
            user_progress: this.userProgress,
            difficulty_preferences: this.getDifficultyPreferences()
        });
        
        this.showLoadingAnimation();
    }
    
    hideAllGameAreas() {
        const gameAreas = document.querySelectorAll('.game-area');
        gameAreas.forEach(area => area.style.display = 'none');
    }
    
    handleNewChallenge(data) {
        this.currentChallenge = data;
        this.hideLoadingAnimation();
        
        switch(this.currentGame) {
            case 'vocabulary':
                this.loadVocabularyChallenge(data);
                break;
            case 'pronunciation':
                this.loadPronunciationChallenge(data);
                break;
            case 'sentence':
                this.loadSentenceChallenge(data);
                break;
            case 'story':
                this.loadStoryChallenge(data);
                break;
        }
    }
    
    loadVocabularyChallenge(data) {
        const wordElement = document.getElementById('challengeWord');
        const optionsGrid = document.getElementById('optionsGrid');
        
        wordElement.textContent = data.word;
        wordElement.style.animation = 'bounce 0.6s ease';
        
        optionsGrid.innerHTML = '';
        data.options.forEach((option, index) => {
            const button = document.createElement('button');
            button.className = 'option-btn';
            button.textContent = option;
            button.onclick = () => this.checkVocabularyAnswer(option, data.correct_answer);
            optionsGrid.appendChild(button);
        });
        
        // Add word pronunciation
        this.speakText(data.word);
    }
    
    loadPronunciationChallenge(data) {
        const wordElement = document.getElementById('pronunciationWord');
        wordElement.textContent = data.word;
        wordElement.style.animation = 'bounce 0.6s ease';
        
        // Clear previous feedback
        document.getElementById('pronunciationFeedback').innerHTML = '';
        
        // Auto-play the word
        setTimeout(() => this.speakText(data.word), 500);
    }
    
    loadSentenceChallenge(data) {
        const promptElement = document.getElementById('sentencePrompt');
        const wordBank = document.getElementById('wordBank');
        const sentenceArea = document.getElementById('sentenceArea');
        
        promptElement.textContent = data.prompt;
        
        // Clear previous content
        wordBank.innerHTML = '';
        sentenceArea.innerHTML = '<p style="color: #999; font-style: italic;">Drag words here to build your sentence...</p>';
        
        // Add word tokens
        data.words.forEach(word => {
            const token = document.createElement('div');
            token.className = 'word-token';
            token.textContent = word;
            token.draggable = true;
            token.onclick = () => this.addWordToSentence(word, token);
            wordBank.appendChild(token);
        });
    }
    
    loadStoryChallenge(data) {
        const storyText = document.getElementById('storyText');
        const storyOptions = document.getElementById('storyOptions');
        
        storyText.innerHTML = data.story_text;
        
        storyOptions.innerHTML = '';
        data.options.forEach(option => {
            const button = document.createElement('button');
            button.className = 'option-btn';
            button.textContent = option;
            button.onclick = () => this.checkStoryAnswer(option, data.correct_answer);
            storyOptions.appendChild(button);
        });
    }
    
    checkVocabularyAnswer(selectedAnswer, correctAnswer) {
        const isCorrect = selectedAnswer === correctAnswer;
        
        // Send answer for AI analysis
        this.socket.emit('submit_answer', {
            game_type: 'vocabulary',
            question: this.currentChallenge.word,
            user_answer: selectedAnswer,
            correct_answer: correctAnswer,
            response_time: Date.now() - this.challengeStartTime
        });
        
        this.handleAnswerResult(isCorrect);
        
        // Visual feedback
        const buttons = document.querySelectorAll('#optionsGrid .option-btn');
        buttons.forEach(btn => {
            if (btn.textContent === selectedAnswer) {
                btn.classList.add(isCorrect ? 'correct' : 'wrong');
            }
            if (btn.textContent === correctAnswer && !isCorrect) {
                btn.classList.add('correct');
            }
            btn.disabled = true;
        });
        
        setTimeout(() => {
            if (this.lives > 0) {
                this.nextChallenge();
            } else {
                this.endGame();
            }
        }, 2000);
    }
    
    checkStoryAnswer(selectedAnswer, correctAnswer) {
        const isCorrect = selectedAnswer === correctAnswer;
        
        this.socket.emit('submit_answer', {
            game_type: 'story',
            question: this.currentChallenge.story_text,
            user_answer: selectedAnswer,
            correct_answer: correctAnswer,
            response_time: Date.now() - this.challengeStartTime
        });
        
        this.handleAnswerResult(isCorrect);
        
        // Visual feedback
        const buttons = document.querySelectorAll('#storyOptions .option-btn');
        buttons.forEach(btn => {
            if (btn.textContent === selectedAnswer) {
                btn.classList.add(isCorrect ? 'correct' : 'wrong');
            }
            if (btn.textContent === correctAnswer && !isCorrect) {
                btn.classList.add('correct');
            }
            btn.disabled = true;
        });
        
        setTimeout(() => {
            if (this.lives > 0) {
                this.nextChallenge();
            } else {
                this.endGame();
            }
        }, 2000);
    }
    
    addWordToSentence(word, token) {
        if (token.classList.contains('used')) return;
        
        const sentenceArea = document.getElementById('sentenceArea');
        
        // Remove placeholder text if present
        if (sentenceArea.querySelector('p')) {
            sentenceArea.innerHTML = '';
        }
        
        // Add word to sentence
        const placedWord = document.createElement('div');
        placedWord.className = 'placed-word';
        placedWord.textContent = word;
        placedWord.onclick = () => this.removeWordFromSentence(word, placedWord, token);
        sentenceArea.appendChild(placedWord);
        
        // Mark token as used
        token.classList.add('used');
    }
    
    removeWordFromSentence(word, placedWord, originalToken) {
        placedWord.remove();
        originalToken.classList.remove('used');
        
        // Add placeholder if sentence is empty
        const sentenceArea = document.getElementById('sentenceArea');
        if (sentenceArea.children.length === 0) {
            sentenceArea.innerHTML = '<p style="color: #999; font-style: italic;">Drag words here to build your sentence...</p>';
        }
    }
    
    checkSentence() {
        const sentenceArea = document.getElementById('sentenceArea');
        const placedWords = Array.from(sentenceArea.querySelectorAll('.placed-word'))
                                .map(word => word.textContent);
        
        if (placedWords.length === 0) {
            this.showFeedback('Please build a sentence first!', 'wrong');
            return;
        }
        
        const userSentence = placedWords.join(' ');
        
        // Send to AI for analysis
        this.socket.emit('check_sentence', {
            user_sentence: userSentence,
            target_prompt: this.currentChallenge.prompt,
            expected_words: this.currentChallenge.expected_words
        });
    }
    
    playWord() {
        if (this.currentChallenge && this.currentChallenge.word) {
            this.speakText(this.currentChallenge.word);
        }
    }
    
    recordPronunciation() {
        if (!this.speechRecognition) {
            this.showFeedback('Speech recognition not supported', 'wrong');
            return;
        }
        
        const recordBtn = document.querySelector('.record-btn');
        
        if (!this.isRecording) {
            this.isRecording = true;
            recordBtn.classList.add('recording');
            recordBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Recording';
            
            this.speechRecognition.start();
            this.challengeStartTime = Date.now();
        } else {
            this.isRecording = false;
            recordBtn.classList.remove('recording');
            recordBtn.innerHTML = '<i class="fas fa-microphone"></i> Record';
            
            this.speechRecognition.stop();
        }
    }
    
    handleSpeechResult(result) {
        const feedbackDiv = document.getElementById('pronunciationFeedback');
        const targetWord = this.currentChallenge.word.toLowerCase();
        const spokenWord = result.toLowerCase().trim();
        
        // Send to AI for pronunciation analysis
        this.socket.emit('analyze_pronunciation', {
            target_word: targetWord,
            spoken_word: spokenWord,
            audio_confidence: 0.8, // This would come from actual audio analysis
            user_id: window.userId || 'guest'
        });
        
        // Basic similarity check
        const similarity = this.calculateSimilarity(targetWord, spokenWord);
        const isCorrect = similarity > 0.7;
        
        feedbackDiv.innerHTML = `
            <div class="pronunciation-result ${isCorrect ? 'correct' : 'wrong'}">
                <h3>${isCorrect ? '🎉 Great!' : '🤔 Try Again'}</h3>
                <p>You said: "<strong>${result}</strong>"</p>
                <p>Target: "<strong>${this.currentChallenge.word}</strong>"</p>
                <p>Accuracy: ${Math.round(similarity * 100)}%</p>
            </div>
        `;
        
        this.handleAnswerResult(isCorrect);
        
        setTimeout(() => {
            if (this.lives > 0) {
                this.nextChallenge();
            } else {
                this.endGame();
            }
        }, 3000);
    }
    
    handleSpeechError(error) {
        const feedbackDiv = document.getElementById('pronunciationFeedback');
        feedbackDiv.innerHTML = `
            <div class="pronunciation-result wrong">
                <h3>🎤 Microphone Issue</h3>
                <p>Please check your microphone and try again.</p>
            </div>
        `;
        
        this.isRecording = false;
        const recordBtn = document.querySelector('.record-btn');
        recordBtn.classList.remove('recording');
        recordBtn.innerHTML = '<i class="fas fa-microphone"></i> Record';
    }
    
    calculateSimilarity(str1, str2) {
        // Simple Levenshtein distance implementation
        const matrix = [];
        
        for (let i = 0; i <= str2.length; i++) {
            matrix[i] = [i];
        }
        
        for (let j = 0; j <= str1.length; j++) {
            matrix[0][j] = j;
        }
        
        for (let i = 1; i <= str2.length; i++) {
            for (let j = 1; j <= str1.length; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }
        
        const maxLength = Math.max(str1.length, str2.length);
        return 1 - (matrix[str2.length][str1.length] / maxLength);
    }
    
    handleAnswerResult(isCorrect) {
        if (isCorrect) {
            this.score += 10 * (this.currentLevel + this.streak);
            this.streak++;
            this.showFeedback('🎉 Excellent! Keep it up!', 'correct');
            
            // Pet encouragement
            const encouragements = [
                "Amazing work! Your pet is so proud! 🌟",
                "Fantastic! You're getting stronger! 💪",
                "Brilliant! Your pet is doing a happy dance! 🎉",
                "Outstanding! You're a language champion! 👑"
            ];
            setTimeout(() => {
                this.showPetEncouragement(encouragements[Math.floor(Math.random() * encouragements.length)]);
            }, 1000);
            
        } else {
            this.lives--;
            this.streak = 0;
            this.showFeedback('💭 Don\'t worry, try again!', 'wrong');
            
            // Pet support
            const supportMessages = [
                "It's okay! Your pet believes in you! 💕",
                "No worries! Learning takes practice! 🌱",
                "Keep trying! Your pet is cheering for you! 📣",
                "Everyone makes mistakes! You've got this! 💪"
            ];
            setTimeout(() => {
                this.showPetEncouragement(supportMessages[Math.floor(Math.random() * supportMessages.length)]);
            }, 1000);
        }
        
        this.updateScoreDisplay();
        this.updateProgressBar();
        
        // Send progress to server for real-time adaptation
        this.socket.emit('update_learning_progress', {
            game_type: this.currentGame,
            score: this.score,
            streak: this.streak,
            lives: this.lives,
            correct: isCorrect,
            difficulty: this.currentLevel
        });
    }
    
    handleAIFeedback(data) {
        // Handle AI-generated feedback and suggestions
        if (data.feedback_type === 'sentence_analysis') {
            const isCorrect = data.is_correct;
            const feedback = data.feedback_message;
            
            this.showFeedback(feedback, isCorrect ? 'correct' : 'wrong');
            this.handleAnswerResult(isCorrect);
            
            setTimeout(() => {
                if (this.lives > 0) {
                    this.nextChallenge();
                } else {
                    this.endGame();
                }
            }, 3000);
        }
        
        if (data.feedback_type === 'pronunciation_analysis') {
            const feedbackDiv = document.getElementById('pronunciationFeedback');
            feedbackDiv.innerHTML += `
                <div class="ai-feedback">
                    <h4>🤖 AI Coach Says:</h4>
                    <p>${data.feedback_message}</p>
                    ${data.pronunciation_tips ? `<p><strong>Tip:</strong> ${data.pronunciation_tips}</p>` : ''}
                </div>
            `;
        }
    }
    
    adjustDifficulty(data) {
        this.currentLevel = data.new_level;
        
        // Update UI to reflect new difficulty
        document.querySelector('.level-indicator').innerHTML = `
            <i class="fas fa-star"></i> Level ${this.currentLevel} | 
            <i class="fas fa-coins"></i> ${data.tokens || 0} Tokens
        `;
        
        this.showFeedback(`Level ${data.adjustment === 'up' ? 'Up' : 'Down'}! ${data.message}`, 'correct');
    }
    
    showPetReaction(data) {
        // Animate pet based on performance
        const petDiv = document.getElementById('petEncouragement');
        const petImg = petDiv.querySelector('.pet-avatar');
        
        switch(data.reaction_type) {
            case 'happy':
                petImg.style.animation = 'bounce 1s ease infinite';
                break;
            case 'excited':
                petImg.style.animation = 'pulse 0.5s ease infinite';
                break;
            case 'encouraging':
                petImg.style.animation = 'shake 0.5s ease';
                break;
        }
        
        setTimeout(() => {
            petImg.style.animation = '';
        }, 3000);
    }
    
    nextChallenge() {
        // Clear previous content and get new challenge
        this.challengeStartTime = Date.now();
        
        this.socket.emit('request_language_challenge', {
            game_type: this.currentGame,
            user_level: this.currentLevel,
            user_progress: this.userProgress,
            previous_performance: {
                correct: this.streak > 0,
                response_time: Date.now() - this.challengeStartTime
            }
        });
        
        this.showLoadingAnimation();
    }
    
    endGame() {
        // Calculate final score and achievements
        const totalScore = this.score;
        const maxStreak = this.streak;
        
        // Send final results to server
        this.socket.emit('game_completed', {
            game_type: this.currentGame,
            final_score: totalScore,
            max_streak: maxStreak,
            total_questions: this.userProgress.total_questions || 0,
            completion_time: Date.now() - this.gameStartTime
        });
        
        // Show game over screen
        this.showGameOverScreen(totalScore, maxStreak);
    }
    
    showGameOverScreen(score, streak) {
        const gameArea = document.querySelector('.game-area[style*="block"]');
        gameArea.innerHTML = `
            <div class="game-over-screen" style="text-align: center;">
                <h2>🎉 Game Complete! 🎉</h2>
                <div class="final-stats">
                    <div class="stat-item">
                        <i class="fas fa-trophy"></i>
                        <h3>Final Score</h3>
                        <p>${score}</p>
                    </div>
                    <div class="stat-item">
                        <i class="fas fa-fire"></i>
                        <h3>Best Streak</h3>
                        <p>${streak}</p>
                    </div>
                    <div class="stat-item">
                        <i class="fas fa-star"></i>
                        <h3>Level Reached</h3>
                        <p>${this.currentLevel}</p>
                    </div>
                </div>
                <div class="game-over-actions">
                    <button class="option-btn" onclick="gameEngine.restartGame()">
                        <i class="fas fa-redo"></i> Play Again
                    </button>
                    <button class="option-btn" onclick="gameEngine.goHome()">
                        <i class="fas fa-home"></i> Dashboard
                    </button>
                </div>
                <div class="achievements" id="gameAchievements">
                    <!-- Achievements will be loaded here -->
                </div>
            </div>
        `;
        
        // Show pet celebration
        setTimeout(() => {
            this.showPetEncouragement("🎉 Fantastic game! Your pet earned new treats! 🍯");
        }, 1000);
    }
    
    restartGame() {
        // Reset game state
        this.score = 0;
        this.streak = 0;
        this.lives = 3;
        this.currentLevel = Math.max(1, this.currentLevel - 1); // Slight difficulty reduction
        
        // Show game modes again
        this.hideAllGameAreas();
        document.getElementById('gameModes').style.display = 'grid';
        
        this.updateScoreDisplay();
        this.updateProgressBar();
    }
    
    goHome() {
        window.location.href = '/dashboard';
    }
    
    updateScoreDisplay() {
        document.getElementById('currentScore').textContent = this.score;
        document.getElementById('currentStreak').textContent = this.streak;
        document.getElementById('livesLeft').textContent = this.lives;
    }
    
    updateProgressBar() {
        const progress = Math.min(100, (this.score / (this.currentLevel * 100)) * 100);
        document.getElementById('progressBar').style.width = progress + '%';
    }
    
    showFeedback(message, type) {
        const feedbackDiv = document.getElementById('feedbackMessage');
        feedbackDiv.textContent = message;
        feedbackDiv.className = `feedback-message feedback-${type}`;
        feedbackDiv.style.display = 'block';
        
        setTimeout(() => {
            feedbackDiv.style.display = 'none';
        }, 3000);
    }
    
    showPetEncouragement(message) {
        const petDiv = document.getElementById('petEncouragement');
        const petMessage = document.getElementById('petMessage');
        petMessage.textContent = message;
        petDiv.style.display = 'block';
        
        setTimeout(() => {
            petDiv.style.display = 'none';
        }, 4000);
    }
    
    showLoadingAnimation() {
        const activeGame = document.querySelector('.game-area[style*="block"]');
        if (activeGame) {
            activeGame.innerHTML = `
                <div class="loading-animation" style="text-align: center; padding: 50px;">
                    <div class="spinner" style="border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto;"></div>
                    <h3>🤖 AI is preparing your challenge...</h3>
                    <p>Personalizing difficulty based on your progress!</p>
                </div>
                <style>
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
            `;
        }
    }
    
    hideLoadingAnimation() {
        // Loading will be replaced by new challenge content
    }
    
    speakText(text) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.8;
            utterance.pitch = 1.1;
            utterance.volume = 0.8;
            
            // Try to use a child-friendly voice
            const voices = speechSynthesis.getVoices();
            const childVoice = voices.find(voice => 
                voice.name.includes('child') || 
                voice.name.includes('young') ||
                voice.pitch > 1.0
            );
            
            if (childVoice) {
                utterance.voice = childVoice;
            }
            
            speechSynthesis.speak(utterance);
        }
    }
    
    loadUserProgress() {
        // Load from localStorage for offline capability
        const savedProgress = localStorage.getItem('languageGameProgress');
        if (savedProgress) {
            this.userProgress = JSON.parse(savedProgress);
        }
    }
    
    saveUserProgress() {
        // Save to localStorage for offline capability
        localStorage.setItem('languageGameProgress', JSON.stringify(this.userProgress));
    }
    
    getDifficultyPreferences() {
        return {
            preferred_topics: this.userProgress.preferred_topics || ['animals', 'colors', 'family'],
            strength_areas: this.userProgress.strength_areas || [],
            challenge_areas: this.userProgress.challenge_areas || [],
            learning_style: this.userProgress.learning_style || 'visual'
        };
    }
    
    updateProgress(data) {
        this.userProgress = { ...this.userProgress, ...data };
        this.saveUserProgress();
        
        // Update UI elements
        if (data.tokens_earned) {
            document.querySelector('.level-indicator').innerHTML = `
                <i class="fas fa-star"></i> Level ${this.currentLevel} | 
                <i class="fas fa-coins"></i> ${data.total_tokens} Tokens
            `;
        }
        
        if (data.achievements) {
            this.showNewAchievements(data.achievements);
        }
    }
    
    showNewAchievements(achievements) {
        achievements.forEach(achievement => {
            const achievementDiv = document.createElement('div');
            achievementDiv.className = 'achievement-popup';
            achievementDiv.innerHTML = `
                <div class="achievement-content">
                    <h3>🏆 New Achievement!</h3>
                    <h4>${achievement.name}</h4>
                    <p>${achievement.description}</p>
                </div>
            `;
            achievementDiv.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                z-index: 1000;
                animation: slideInRight 0.5s ease;
            `;
            
            document.body.appendChild(achievementDiv);
            
            setTimeout(() => {
                achievementDiv.remove();
            }, 5000);
        });
    }
}

// Global functions
function startGame(gameType) {
    if (window.gameEngine) {
        window.gameEngine.gameStartTime = Date.now();
        window.gameEngine.startGame(gameType);
    }
}

function playWord() {
    if (window.gameEngine) {
        window.gameEngine.playWord();
    }
}

function recordPronunciation() {
    if (window.gameEngine) {
        window.gameEngine.recordPronunciation();
    }
}

function checkSentence() {
    if (window.gameEngine) {
        window.gameEngine.checkSentence();
    }
}

function goHome() {
    window.location.href = '/dashboard';
}

// Initialize game engine when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.gameEngine = new LanguageGameEngine();
    
    // Add some CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .final-stats {
            display: flex;
            justify-content: space-around;
            margin: 30px 0;
        }
        
        .stat-item {
            text-align: center;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            margin: 0 10px;
        }
        
        .stat-item i {
            font-size: 2rem;
            margin-bottom: 10px;
            color: #667eea;
        }
        
        .game-over-actions {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin: 30px 0;
        }
        
        .pronunciation-result {
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            text-align: center;
        }
        
        .pronunciation-result.correct {
            background: linear-gradient(45deg, #56ab2f 0%, #a8e6cf 100%);
            color: white;
        }
        
        .pronunciation-result.wrong {
            background: linear-gradient(45deg, #ff416c 0%, #ff4b2b 100%);
            color: white;
        }
        
        .ai-feedback {
            background: rgba(102, 126, 234, 0.1);
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 15px 0;
            border-radius: 10px;
        }
        
        .ai-feedback h4 {
            color: #667eea;
            margin-bottom: 10px;
        }
    `;
    document.head.appendChild(style);
});