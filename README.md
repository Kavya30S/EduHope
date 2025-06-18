```markdown
# EduHope (Flask Mobile App)

EduHope is a zero-cost, open-source mobile application designed to provide personalized education, emotional support, and social connection for children in conflict zones. With a gamified, interactive interface, EduHope fosters learning and resilience in challenging environments using open-source technologies. This README guides you through the app’s functionality, structure, data sources, dependencies, and setup instructions.

**GitHub Repository**: [github.com/Kavya30S/EduHope](https://github.com/Kavya30S/EduHope)

## Table of Contents

- [Project Overview](#project-overview)
- [General Flow](#general-flow)
- [Folder Structure](#folder-structure)
- [Dataset Acquisition](#dataset-acquisition)
- [Dependencies and Technologies](#dependencies-and-technologies)
- [Problem and Solution](#problem-and-solution)
- [Key Features](#key-features)
- [Step-by-Step Setup](#step-by-step-setup)
- [Troubleshooting](#troubleshooting)
- [Collaborators](#collaborators)
- [Contributing](#contributing)
- [Contact](#contact)

## Project Overview

EduHope addresses the educational and emotional needs of children in conflict zones, where access to schooling, resources, and social interaction is disrupted. By leveraging a Flask-based backend, AI-driven content generation, and offline capabilities, the app delivers a fun, engaging platform for learning, emotional support, and peer collaboration. Tailored for low-connectivity environments, EduHope uses open-source datasets and local models to ensure accessibility and scalability.

### Mission
- Empower Education: Deliver personalized lessons based on age, language, and interests.
- Foster Resilience: Provide trauma-informed emotional support tools.
- Build Community: Enable safe, gamified social interactions.
- Ensure Accessibility: Support offline use in resource-scarce areas.

## General Flow

The user journey in EduHope is intuitive and engaging, designed to keep children motivated:

```plaintext
Login → Assessment Games → Dashboard → Pet Companion → Collaborative Storytelling → Language Games → Logout
```

- **Login**: Users authenticate to access personalized features.
- **Assessment Games**: New users play fun games to evaluate knowledge and emotional state, replacing traditional forms.
- **Dashboard**: Central hub for navigating features and tracking progress.
- **Pet Companion**: Interact with a virtual pet that grows with learning and care.
- **Collaborative Storytelling**: Co-create stories with peers for creativity and connection.
- **Language Games**: Learn languages through interactive challenges.
- **Logout**: Securely exit the app.

## Folder Structure

The project is organized for modularity and clarity. Below is the folder structure with descriptions.

### Directory Details

```plaintext
EduHope/
├── app/
│   ├── main.py                  # Entry point to run the app
│   ├── models/
│   │   ├── user.py              # User model for authentication and gamified data (points, emotional state)
│   │   ├── lesson.py            # Lesson model for educational content
│   │   ├── achievement.py       # Achievement model for gamification badges
│   │   └── pet.py               # Pet model for Virtual Pet Companion attributes (hunger, happiness)
│   ├── routes/
│   │   ├── auth.py              # Handles login, registration, and logout with assessment redirects
│   │   ├── education.py         # Manages lessons and quizzes
│   │   ├── support.py           # Emotional support features (e.g., mood analysis)
│   │   ├── social.py            # Social interactions (e.g., chat)
│   │   ├── teacher.py           # Teacher tools for progress tracking
│   │   ├── pet_companion.py     # Virtual Pet Companion interactions (feed, play)
│   │   ├── storytelling.py      # Collaborative storytelling with real-time updates
│   │   └── language_games.py    # Language learning games with speech recognition
│   ├── templates/
│   │   ├── base.html            # Base HTML template with navigation
│   │   ├── login.html           # Login page
│   │   ├── dashboard.html       # User dashboard for feature access
│   │   ├── lesson.html          # Displays educational lessons
│   │   ├── chat.html            # Social chat interface
│   │   ├── game.html            # General game interface
│   │   ├── pet.html             # Virtual Pet Companion interface
│   │   ├── storytelling.html    # Collaborative storytelling interface
│   │   └── language_game.html   # Language learning game interface
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # Styling for a playful, soothing UI
│   │   ├── js/
│   │   │   ├── main.js          # Service worker registration and general JS
│   │   │   ├── math_maze.js     # Math-based game logic
│   │   │   ├── pet.js           # Pet interaction scripts
│   │   │   ├── storytelling.js  # Real-time storytelling scripts
│   │   │   └── language_game.js # Language game logic
│   │   └── images/
│   │       └── logo.png         # App logo
│   ├── services/
│   │   ├── llm_service.py       # LLM (GPT-2) for lesson and story suggestions
│   │   ├── voice_service.py     # Speech-to-text for language games
│   │   ├── translation_service.py # Translation for multilingual support
│   │   ├── sentiment_service.py  # Sentiment analysis for emotional support
│   │   └── moderation_service.py # Content filtering for safety
│   └── assessment_games/
│       ├── knowledge_assessment.py # Game to assess knowledge level
│       └── emotional_assessment.py # Game to assess emotional state
├── data/
│   ├── datasets/
│   │   ├── wikitext/            # WikiText dataset for general knowledge
│   │   └── folktales/           # Folktales for storytelling
│   └── models/
│       └── gpt2_edu/            # Fine-tuned GPT-2 model for education
├── docs/
│   └── README.md                # Project documentation (this file)
├── tests/
│   └── test_main.py             # Unit tests for core functionality
├── requirements.txt             # Python dependencies
├── environment.yml              # Conda environment configuration
└── .gitignore                   # Files to ignore in Git
```

## Dataset Acquisition

EduHope relies on open-source datasets for educational and cultural content. Below are the datasets, their sources, and acquisition steps.

### WikiText (General Knowledge)
- **Source**: [Hugging Face Datasets](https://huggingface.co/datasets/wikitext)
- **Steps**:
  1. Install the `datasets` library:
     ```
     pip install datasets
     ```
  2. Run the following Python script:
     ```python
     from datasets import load_dataset
     dataset = load_dataset("wikitext", "wikitext-103-v1")
     dataset.save_to_disk("data/datasets/wikitext")
     ```
  3. Save in `data/datasets/wikitext/`.

### Folktales (Storytelling)
- **Source**: [Project Gutenberg](https://www.gutenberg.org/)
- **Steps**:
  1. Visit the website and search for “folktales” or “Grimm’s Fairy Tales”.
  2. Download text files (e.g., `.txt` format).
  3. Save in `data/datasets/folktales/`.

### CK-12 FlexBooks (Educational Content)
- **Source**: [CK-12 Foundation](https://www.ck12.org/)
- **Steps**:
  1. Browse “FlexBooks” for subjects like Math or Science.
  2. Download free PDFs or access via their API (if available).
  3. Save in `data/datasets/ck12/`.

### Wikipedia Dumps (Language-Specific Content)
- **Source**: [Wikimedia Dumps](https://dumps.wikimedia.org/)
- **Steps**:
  1. Select a language (e.g., `enwiki` for English).
  2. Download `enwiki-latest-abstract.xml.gz` from the “latest” section.
  3. Extract and save in `data/datasets/wikipedia/`.

### WHO Mental Health Atlas (Emotional Support)
- **Source**: [WHO Mental Health Atlas](https://www.who.int/publications/i/item/9789240036703)
- **Steps**:
  1. Download the free PDF or dataset.
  2. Save in `data/datasets/who/`.

### Tatoeba (Language Learning)
- **Source**: [Tatoeba](https://tatoeba.org/)
- **Steps**:
  1. Download sentence datasets in desired languages (e.g., `.csv`).
  2. Save in `data/datasets/tatoeba/`.

## Dependencies and Technologies

EduHope is built with open-source tools to ensure zero-cost development and deployment. Below is a detailed list of dependencies, APIs, and technologies.

### Python Libraries
- `flask==2.0.1`: Web framework for the app backend.
- `flask-sqlalchemy==2.5.1`: ORM for SQLite database management.
- `flask-login==0.5.0`: User session management for authentication.
- `flask-socketio==5.1.0`: Real-time communication for storytelling and chat.
- `bcrypt==3.2.0`: Password hashing for secure authentication.
- `transformers==4.20.1`: Hugging Face library for GPT-2 model integration.
- `datasets==2.3.2`: Loads datasets like WikiText for content.
- `deepspeech==0.9.3`: Mozilla DeepSpeech for speech recognition in language games.
- `pyttsx3==2.90`: Text-to-speech for accessibility.
- `better-profanity==0.7.0`: Content moderation for safe interactions.

### JavaScript Libraries
- `socket.io==4.0.1`: Client-side real-time communication for live updates.
- `phaser==3.55.2`: Game framework for interactive assessment and language games (optional).

### APIs and Tools
- **LibreTranslate**: Local translation server for multilingual support.
  - Installation: [LibreTranslate GitHub](https://github.com/LibreTranslate/LibreTranslate)
- **DiceBear API**: Free avatar generation for user profiles.
  - URL: [DiceBear](https://www.dicebear.com/)
- **Service Workers**: Browser-based offline caching for low-connectivity areas.

### Technologies
- **SQLite**: Lightweight database for offline storage of user data and progress.
- **HTML5/CSS3/JavaScript**: Frontend for a playful, responsive UI.
- **Conda**: Environment management for reproducible setups.

### Development Tools
- **VS Code**: IDE with Conda integration for development.
- **Anaconda Prompt**: For running Conda commands and managing environments.
- **Git**: Version control for collaborative development.

## Problem and Solution

### Problem Statement
Children in conflict zones face:
- Disrupted Education: Lack of access to schools and resources.
- Emotional Trauma: Psychological challenges from unstable environments.
- Social Isolation: Limited opportunities for peer interaction.
- Resource Scarcity: Low connectivity and technology access hinder learning.

### Solution
EduHope provides a zero-cost, open-source mobile app that delivers:
- Personalized Education: Tailored lessons based on age, language, and interests.
- Emotional Support: Trauma-informed tools to foster resilience.
- Social Connection: Safe, gamified interactions to build community.
- Offline Access: Ensures usability in low-connectivity areas using SQLite and service workers.

## Key Features

### Virtual Pet Companion
- Adopt a pet (e.g., dragon, unicorn, robot) that grows with learning and care.
- Feed, play, and level up to earn badges like “Pet Protector”.
- Pets interact in a virtual playground for social engagement.
- Implementation: `pet.py` model and `pet_companion.py` route with `pet.js` for frontend interactions.

### Collaborative Storytelling
- Co-create stories with peers, with AI suggestions from GPT-2 (`llm_service.py`).
- Earn “Storyteller Points” and vote for “Hall of Fame” stories.
- Share or print illustrated stories.
- Implementation: `storytelling.py` route with SocketIO for real-time updates and `storytelling.js` for client-side logic.

### Language Learning Games
- Interactive games for vocabulary, pronunciation, and sentence building.
- Uses DeepSpeech (`voice_service.py`) for speech recognition and Tatoeba datasets.
- Earn “Language Tokens” to unlock new challenges.
- Implementation: `language_games.py` route and `language_game.js` for game logic.

### Assessment Games
- Fun games post-login to assess knowledge (`knowledge_assessment.py`) and emotional state (`emotional_assessment.py`).
- Replaces traditional forms with engaging quizzes and mood check-ins.
- Implementation: Flask routes and Phaser-based frontend (optional).

### Real-Time and Offline Support
- SocketIO (`flask-socketio`) for live updates (e.g., pet stats, story contributions).
- Service workers (`main.js`) and SQLite (`flask-sqlalchemy`) for offline learning and syncing.

## Step-by-Step Setup

### Prerequisites
- Python 3.8+ and Conda installed (e.g., at `C:\Users\THINKPAD\.conda`).
- Git for cloning the repository.
- VS Code with Python extension for development.
- Internet connection for dataset downloads and dependency installation.

### Step 1: Clone the Repository
1. Open Anaconda Prompt.
2. Navigate to a working directory:
   ```
   cd C:\Users\THINKPAD\Documents
   ```
3. Clone the repository:
   ```
   git clone https://github.com/Kavya30S/EduHope.git
   ```
4. Enter the directory:
   ```
   cd EduHope
   ```

### Step 2: Set Up Conda Environment
1. Create and activate the environment:
   ```
   conda env create -f environment.yml
   conda activate eduhope
   ```
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

### Step 3: Acquire Datasets
- Follow the [Dataset Acquisition](#dataset-acquisition) section to download and save datasets in `data/datasets/`.
- Ensure `data/models/gpt2_edu/` contains the fine-tuned GPT-2 model (download separately if not included).

### Step 4: Run the Application
1. Start the Flask app:
   ```
   python app/main.py
   ```
2. Open `http://localhost:5000` in a browser to access EduHope.
3. Log in or register to explore features.

### Step 5: Verify Functionality
- Test features like login, assessment games, dashboard, pet companion, storytelling, and language games.
- Check `data/` for dataset integrity and SQLite database (`app.db`) for user data.

### Step 6: Push to GitHub
1. Commit changes:
   ```
   git add .
   git commit -m "Updated README formatting"
   git push origin main
   ```

## Collaborators

- Ashwani Dhurve
- Dolly Tripathi
- Kavya Sharma
- Lekhika Sahu

## Troubleshooting

### Dependency Issues
- Verify installed packages:
  ```
  pip show flask flask-sqlalchemy transformers deepspeech
  ```
- Reinstall:
  ```
  pip install -r requirements.txt
  ```

### Dataset Errors
- Ensure datasets are in `data/datasets/` with correct folder names (e.g., `wikitext`, `folktales`).
- Re-run acquisition scripts if files are missing.

### Flask Server Issues
- Ensure port 5000 is free:
  ```
  netstat -aon | findstr :5000
  ```
- Kill conflicting process:
  ```
  taskkill /PID <pid> /F
  ```

### Real-Time Feature Errors
- Check SocketIO installation:
  ```
  pip show flask-socketio
  ```
- Verify `socket.io` in `static/js/main.js`.

### Database Issues
- Delete `app.db` and restart the app to recreate the SQLite database.
- Check `flask-sqlalchemy` configuration in `app/__init__.py`.

---
EduHope is a mission-driven project to empower children through education and connection. Join us in building a brighter future!
```