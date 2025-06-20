from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class EmotionalState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Current emotional metrics
    happiness = db.Column(db.Float, default=50.0)
    stress_level = db.Column(db.Float, default=30.0)
    confidence = db.Column(db.Float, default=50.0)
    motivation = db.Column(db.Float, default=50.0)
    social_connection = db.Column(db.Float, default=40.0)
    
    # Recent emotions (JSON array of recent mood entries)
    recent_moods = db.Column(db.Text, default='[]')
    
    # Triggers and patterns
    positive_triggers = db.Column(db.Text, default='[]')  # What makes them happy
    stress_triggers = db.Column(db.Text, default='[]')    # What causes stress
    
    # Support preferences
    preferred_activities = db.Column(db.Text, default='[]')
    communication_style = db.Column(db.String(50), default='encouraging')  # encouraging, gentle, playful
    
    # Timestamps
    last_check_in = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('emotional_state', uselist=False))
    
    def get_recent_moods(self):
        """Get recent mood entries"""
        try:
            return json.loads(self.recent_moods)
        except:
            return []
    
    def add_mood_entry(self, mood_data):
        """Add new mood entry"""
        moods = self.get_recent_moods()
        mood_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'mood': mood_data.get('mood', 'neutral'),
            'intensity': mood_data.get('intensity', 5),
            'context': mood_data.get('context', ''),
            'activities': mood_data.get('activities', [])
        }
        moods.append(mood_entry)
        
        # Keep only last 50 entries
        if len(moods) > 50:
            moods = moods[-50:]
        
        self.recent_moods = json.dumps(moods)
        self.update_emotional_metrics(mood_data)
    
    def update_emotional_metrics(self, mood_data):
        """Update emotional metrics based on mood entry"""
        mood = mood_data.get('mood', 'neutral')
        intensity = mood_data.get('intensity', 5)
        
        # Happiness adjustments
        if mood in ['happy', 'excited', 'joyful', 'proud']:
            self.happiness = min(100, self.happiness + (intensity * 2))
        elif mood in ['sad', 'angry', 'frustrated', 'disappointed']:
            self.happiness = max(0, self.happiness - intensity)
        
        # Stress level adjustments
        if mood in ['anxious', 'worried', 'overwhelmed', 'frustrated']:
            self.stress_level = min(100, self.stress_level + intensity)
        elif mood in ['calm', 'peaceful', 'relaxed']:
            self.stress_level = max(0, self.stress_level - (intensity * 1.5))
        
        # Confidence adjustments
        if mood in ['proud', 'accomplished', 'confident']:
            self.confidence = min(100, self.confidence + intensity)
        elif mood in ['embarrassed', 'insecure', 'disappointed']:
            self.confidence = max(0, self.confidence - intensity)
        
        # Motivation adjustments
        if mood in ['excited', 'determined', 'inspired']:
            self.motivation = min(100, self.motivation + intensity)
        elif mood in ['bored', 'tired', 'unmotivated']:
            self.motivation = max(0, self.motivation - intensity)
        
        self.last_check_in = datetime.utcnow()
    
    def get_positive_triggers(self):
        """Get list of positive triggers"""
        try:
            return json.loads(self.positive_triggers)
        except:
            return []
    
    def add_positive_trigger(self, trigger):
        """Add positive trigger"""
        triggers = self.get_positive_triggers()
        if trigger not in triggers:
            triggers.append(trigger)
            self.positive_triggers = json.dumps(triggers)
    
    def get_stress_triggers(self):
        """Get list of stress triggers"""
        try:
            return json.loads(self.stress_triggers)
        except:
            return []
    
    def add_stress_trigger(self, trigger):
        """Add stress trigger"""
        triggers = self.get_stress_triggers()
        if trigger not in triggers:
            triggers.append(trigger)
            self.stress_triggers = json.dumps(triggers)
    
    def get_preferred_activities(self):
        """Get preferred activities"""
        try:
            return json.loads(self.preferred_activities)
        except:
            return []
    
    def add_preferred_activity(self, activity):
        """Add preferred activity"""
        activities = self.get_preferred_activities()
        if activity not in activities:
            activities.append(activity)
            self.preferred_activities = json.dumps(activities)
    
    def get_emotional_summary(self):
        """Get overall emotional state summary"""
        overall_score = (self.happiness + (100 - self.stress_level) + self.confidence + self.motivation + self.social_connection) / 5
        
        if overall_score >= 80:
            state = 'Thriving'
            message = "You're doing amazing! Keep up the wonderful work!"
            color = '#4CAF50'
        elif overall_score >= 60:
            state = 'Good'
            message = "You're doing well! A few small steps can make you feel even better."
            color = '#8BC34A'
        elif overall_score >= 40:
            state = 'Okay'
            message = "You're managing okay. Let's work together to brighten your day!"
            color = '#FFC107'
        elif overall_score >= 20:
            state = 'Struggling'
            message = "It seems like you're having a tough time. I'm here to help!"
            color = '#FF9800'
        else:
            state = 'Needs Support'
            message = "You need extra care right now. Let's take it one step at a time."
            color = '#F44336'
        
        return {
            'state': state,
            'score': round(overall_score, 1),
            'message': message,
            'color': color,
            'recommendations': self.get_recommendations()
        }
    
    def get_recommendations(self):
        """Get personalized recommendations based on emotional state"""
        recommendations = []
        
        # Happiness recommendations
        if self.happiness < 40:
            recommendations.append({
                'type': 'happiness',
                'activity': 'Play with your pet',
                'description': 'Spending time with your virtual pet can boost your mood!',
                'icon': '🐾'
            })
            recommendations.append({
                'type': 'happiness',
                'activity': 'Creative storytelling',
                'description': 'Create a fun story with friends to spark joy!',
                'icon': '📚'
            })
        
        # Stress recommendations
        if self.stress_level > 60:
            recommendations.append({
                'type': 'stress',
                'activity': 'Breathing exercise',
                'description': 'Take 5 deep breaths to calm your mind.',
                'icon': '🧘'
            })
            recommendations.append({
                'type': 'stress',
                'activity': 'Gentle games',
                'description': 'Play some relaxing puzzle games.',
                'icon': '🧩'
            })
        
        # Confidence recommendations
        if self.confidence < 40:
            recommendations.append({
                'type': 'confidence',
                'activity': 'Learning achievement',
                'description': 'Complete a lesson to build confidence!',
                'icon': '🏆'
            })
            recommendations.append({
                'type': 'confidence',
                'activity': 'Positive affirmations',
                'description': 'Practice saying kind things about yourself.',
                'icon': '💪'
            })
        
        # Motivation recommendations
        if self.motivation < 40:
            recommendations.append({
                'type': 'motivation',
                'activity': 'Set small goals',
                'description': 'Pick one small task to accomplish today.',
                'icon': '🎯'
            })
            recommendations.append({
                'type': 'motivation',
                'activity': 'Connect with friends',
                'description': 'Chat with other learners for inspiration.',
                'icon': '👥'
            })
        
        # Social connection recommendations
        if self.social_connection < 40:
            recommendations.append({
                'type': 'social',
                'activity': 'Group storytelling',
                'description': 'Join a group story creation session.',
                'icon': '🤝'
            })
            recommendations.append({
                'type': 'social',
                'activity': 'Help others',
                'description': 'Share knowledge with other learners.',
                'icon': '❤️'
            })
        
        return recommendations[:4]  # Return top 4 recommendations
    
    def get_mood_patterns(self):
        """Analyze mood patterns over time"""
        moods = self.get_recent_moods()
        if not moods:
            return {'pattern': 'insufficient_data', 'message': 'We need more mood check-ins to see patterns.'}
        
        # Get last 7 days of moods
        recent_moods = moods[-20:]  # Approximate last week
        
        # Count mood types
        mood_counts = {}
        total_intensity = 0
        
        for mood_entry in recent_moods:
            mood = mood_entry.get('mood', 'neutral')
            intensity = mood_entry.get('intensity', 5)
            
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
            total_intensity += intensity
        
        if not mood_counts:
            return {'pattern': 'no_data', 'message': 'No recent mood data available.'}
        
        # Find dominant mood
        dominant_mood = max(mood_counts, key=mood_counts.get)
        avg_intensity = total_intensity / len(recent_moods)
        
        # Analyze trend
        if len(recent_moods) >= 10:
            first_half = recent_moods[:len(recent_moods)//2]
            second_half = recent_moods[len(recent_moods)//2:]
            
            first_avg = sum(m.get('intensity', 5) for m in first_half) / len(first_half)
            second_avg = sum(m.get('intensity', 5) for m in second_half) / len(second_half)
            
            if second_avg > first_avg + 1:
                trend = 'improving'
            elif second_avg < first_avg - 1:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'dominant_mood': dominant_mood,
            'average_intensity': round(avg_intensity, 1),
            'trend': trend,
            'mood_distribution': mood_counts,
            'total_entries': len(recent_moods)
        }
    
    def to_dict(self):
        """Convert emotional state to dictionary"""
        return {
            'happiness': self.happiness,
            'stress_level': self.stress_level,
            'confidence': self.confidence,
            'motivation': self.motivation,
            'social_connection': self.social_connection,
            'recent_moods': self.get_recent_moods(),
            'positive_triggers': self.get_positive_triggers(),
            'stress_triggers': self.get_stress_triggers(),
            'preferred_activities': self.get_preferred_activities(),
            'communication_style': self.communication_style,
            'emotional_summary': self.get_emotional_summary(),
            'mood_patterns': self.get_mood_patterns(),
            'last_check_in': self.last_check_in.isoformat() if self.last_check_in else None
        }


class SupportSession(db.Model):
    """Track emotional support sessions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    session_type = db.Column(db.String(50), nullable=False)  # chat, breathing, activity, etc.
    duration_minutes = db.Column(db.Integer, default=0)
    
    # Session data
    initial_mood = db.Column(db.String(50))
    final_mood = db.Column(db.String(50))
    activities_completed = db.Column(db.Text, default='[]')  # JSON array
    
    # Effectiveness
    helpfulness_rating = db.Column(db.Integer)  # 1-5 scale
    user_feedback = db.Column(db.Text)
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('support_sessions', lazy=True))
    
    def get_activities_completed(self):
        """Get list of completed activities"""
        try:
            return json.loads(self.activities_completed)
        except:
            return []
    
    def add_completed_activity(self, activity):
        """Add completed activity"""
        activities = self.get_activities_completed()
        activities.append({
            'activity': activity,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.activities_completed = json.dumps(activities)
    
    def complete_session(self, final_mood, helpfulness_rating=None, feedback=None):
        """Complete the support session"""
        self.final_mood = final_mood
        self.completed_at = datetime.utcnow()
        if helpfulness_rating:
            self.helpfulness_rating = helpfulness_rating
        if feedback:
            self.user_feedback = feedback
        
        # Calculate duration
        if self.started_at and self.completed_at:
            duration = self.completed_at - self.started_at
            self.duration_minutes = int(duration.total_seconds() / 60)
    
    def to_dict(self):
        """Convert support session to dictionary"""
        return {
            'id': self.id,
            'session_type': self.session_type,
            'duration_minutes': self.duration_minutes,
            'initial_mood': self.initial_mood,
            'final_mood': self.final_mood,
            'activities_completed': self.get_activities_completed(),
            'helpfulness_rating': self.helpfulness_rating,
            'user_feedback': self.user_feedback,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }