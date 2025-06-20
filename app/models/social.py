from datetime import datetime
from app import db
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

class Chat(db.Model):
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    room_id = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(50), default='text')  # text, image, pet_action, story_share
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_moderated = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)
    reactions = relationship('ChatReaction', backref='chat', lazy='dynamic', cascade='all, delete-orphan')
    
    # Relationship with User
    user = relationship('User', backref='chats')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'room_id': self.room_id,
            'message': self.message,
            'message_type': self.message_type,
            'timestamp': self.timestamp.isoformat(),
            'is_moderated': self.is_moderated,
            'reactions': [r.to_dict() for r in self.reactions]
        }

class ChatReaction(db.Model):
    __tablename__ = 'chat_reactions'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reaction_type = Column(String(50), nullable=False)  # heart, star, laugh, surprise
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', backref='chat_reactions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'reaction_type': self.reaction_type,
            'timestamp': self.timestamp.isoformat()
        }

class SocialGroup(db.Model):
    __tablename__ = 'social_groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    max_members = Column(Integer, default=10)
    group_type = Column(String(50), default='study')  # study, pet_playdate, storytelling
    
    # Relationships
    creator = relationship('User', backref='created_groups')
    members = relationship('GroupMember', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else 'Unknown',
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'member_count': self.members.count(),
            'max_members': self.max_members,
            'group_type': self.group_type
        }

class GroupMember(db.Model):
    __tablename__ = 'group_members'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('social_groups.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String(50), default='member')  # member, moderator, admin
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship('User', backref='group_memberships')
    
    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'joined_at': self.joined_at.isoformat(),
            'role': self.role,
            'is_active': self.is_active
        }

class FriendRequest(db.Model):
    __tablename__ = 'friend_requests'
    
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(20), default='pending')  # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime)
    
    # Relationships
    sender = relationship('User', foreign_keys=[sender_id], backref='sent_friend_requests')
    receiver = relationship('User', foreign_keys=[receiver_id], backref='received_friend_requests')
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.username if self.sender else 'Unknown',
            'receiver_id': self.receiver_id,
            'receiver_name': self.receiver.username if self.receiver else 'Unknown',
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'responded_at': self.responded_at.isoformat() if self.responded_at else None
        }

class Friendship(db.Model):
    __tablename__ = 'friendships'
    
    id = Column(Integer, primary_key=True)
    user1_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user2_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user1 = relationship('User', foreign_keys=[user1_id], backref='friendships_as_user1')
    user2 = relationship('User', foreign_keys=[user2_id], backref='friendships_as_user2')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user1_id': self.user1_id,
            'user1_name': self.user1.username if self.user1 else 'Unknown',
            'user2_id': self.user2_id,
            'user2_name': self.user2.username if self.user2 else 'Unknown',
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }

# Social Activity Tracking
class SocialActivity(db.Model):
    __tablename__ = 'social_activities'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    activity_type = Column(String(50), nullable=False)  # message_sent, friend_made, group_joined, story_shared
    activity_data = Column(Text)  # JSON string with additional data
    timestamp = Column(DateTime, default=datetime.utcnow)
    points_earned = Column(Integer, default=0)
    
    # Relationships
    user = relationship('User', backref='social_activities')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'activity_data': self.activity_data,
            'timestamp': self.timestamp.isoformat(),
            'points_earned': self.points_earned
        }