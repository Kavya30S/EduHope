from app import db
from datetime import datetime

class CounselorConversation(db.Model):
    """
    Database model for storing virtual counselor conversation history.
    """
    __tablename__ = 'counselor_conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    counselor_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Define relationship with User model (assuming it exists)
    user = db.relationship('User', backref=db.backref('conversations', lazy=True))

    def __init__(self, user_id, user_message, counselor_response):
        """
        Initialize a new conversation entry.
        
        Args:
            user_id (int): The ID of the user.
            user_message (str): The message sent by the user.
            counselor_response (str): The response from the virtual counselor.
        """
        self.user_id = user_id
        self.user_message = user_message
        self.counselor_response = counselor_response

    def __repr__(self):
        return f'<CounselorConversation user_id={self.user_id}, timestamp={self.timestamp}>'