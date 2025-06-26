from app import db
from datetime import datetime

class JournalEntry(db.Model):
    """
    Database model for storing user journal entries.
    """
    __tablename__ = 'journal_entries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=False)
    mood = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Define relationship with User model (assuming it exists)
    user = db.relationship('User', backref=db.backref('journal_entries', lazy=True))

    def __init__(self, user_id, content, title=None, mood=None):
        """
        Initialize a new journal entry.
        
        Args:
            user_id (int): The ID of the user.
            content (str): The content of the journal entry.
            title (str, optional): The title of the journal entry.
            mood (str, optional): The mood associated with the journal entry.
        """
        self.user_id = user_id
        self.title = title
        self.content = content
        self.mood = mood

    def __repr__(self):
        return f'<JournalEntry user_id={self.user_id}, timestamp={self.timestamp}>'