from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from app import db, socketio
from app.models.user import User
from app.models.pet import Pet
from app.services.moderation_service import ModerationService
import json
from datetime import datetime

social_bp = Blueprint('social', __name__, url_prefix='/social')
moderation = ModerationService()

# Active chat rooms and users
active_rooms = {}
user_rooms = {}

@social_bp.route('/chat')
@login_required
def chat():
    """Main chat interface for children"""
    return render_template('chat.html', user=current_user)

@social_bp.route('/playground')
@login_required
def playground():
    """Virtual playground where pets can interact"""
    # Get all active pets in playground
    active_pets = Pet.query.join(User).filter(
        User.last_active > datetime.utcnow() - timedelta(minutes=30)
    ).all()
    
    return render_template('playground.html', 
                         user=current_user, 
                         active_pets=active_pets)

@social_bp.route('/friends')
@login_required
def friends():
    """Friends management page"""
    # Get potential friends (users with similar interests/age)
    potential_friends = User.query.filter(
        User.id != current_user.id,
        User.age.between(current_user.age - 2, current_user.age + 2)
    ).limit(10).all()
    
    return render_template('friends.html', 
                         user=current_user,
                         potential_friends=potential_friends)

@social_bp.route('/send_friend_request', methods=['POST'])
@login_required
def send_friend_request():
    """Send a friend request to another user"""
    data = request.get_json()
    friend_id = data.get('friend_id')
    
    if not friend_id:
        return jsonify({'success': False, 'message': 'Friend ID required'})
    
    friend = User.query.get(friend_id)
    if not friend:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Check if already friends or request exists
    if friend in current_user.friends:
        return jsonify({'success': False, 'message': 'Already friends!'})
    
    # Add to friend requests (simplified - in production use a proper relationship table)
    if not hasattr(current_user, 'friend_requests_sent'):
        current_user.friend_requests_sent = []
    
    current_user.friend_requests_sent.append(friend_id)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Friend request sent! 🌟'})

# Socket.IO events for real-time chat
@socketio.on('join_chat')
def handle_join_chat(data):
    """Handle user joining a chat room"""
    room = data.get('room', 'general')
    username = current_user.username if current_user.is_authenticated else 'Anonymous'
    
    join_room(room)
    user_rooms[request.sid] = room
    
    if room not in active_rooms:
        active_rooms[room] = set()
    active_rooms[room].add(username)
    
    emit('user_joined', {
        'username': username,
        'message': f'{username} joined the magical chat! ✨',
        'timestamp': datetime.now().strftime('%H:%M'),
        'users_count': len(active_rooms[room])
    }, room=room)

@socketio.on('leave_chat')
def handle_leave_chat(data):
    """Handle user leaving a chat room"""
    room = user_rooms.get(request.sid, 'general')
    username = current_user.username if current_user.is_authenticated else 'Anonymous'
    
    leave_room(room)
    
    if room in active_rooms and username in active_rooms[room]:
        active_rooms[room].remove(username)
        
        emit('user_left', {
            'username': username,
            'message': f'{username} left the chat. See you soon! 👋',
            'timestamp': datetime.now().strftime('%H:%M'),
            'users_count': len(active_rooms[room])
        }, room=room)

@socketio.on('send_message')
def handle_message(data):
    """Handle sending a chat message"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Please log in to chat!'})
        return
    
    room = data.get('room', 'general')
    message = data.get('message', '').strip()
    
    if not message:
        return
    
    # Moderate the message
    if not moderation.is_safe_message(message):
        emit('message_blocked', {
            'message': 'Your message contains inappropriate content. Let\'s keep our chat friendly! 🌈'
        })
        return
    
    # Add some fun reactions based on keywords
    reactions = []
    if any(word in message.lower() for word in ['happy', 'excited', 'great', 'awesome']):
        reactions.append('😄')
    if any(word in message.lower() for word in ['learn', 'study', 'homework']):
        reactions.append('📚')
    if any(word in message.lower() for word in ['pet', 'dragon', 'unicorn']):
        reactions.append('🐉')
    
    # Store message in database (simplified)
    message_data = {
        'username': current_user.username,
        'message': message,
        'timestamp': datetime.now().strftime('%H:%M'),
        'user_level': current_user.level,
        'pet_emoji': current_user.pet.pet_type.emoji if current_user.pet else '🌟',
        'reactions': reactions
    }
    
    emit('new_message', message_data, room=room)
    
    # Award points for positive social interaction
    current_user.add_points(2, 'social_chat')
    db.session.commit()

@socketio.on('pet_interaction')
def handle_pet_interaction(data):
    """Handle pet interactions in the playground"""
    if not current_user.is_authenticated or not current_user.pet:
        return
    
    interaction_type = data.get('type')  # 'play', 'greet', 'dance'
    target_pet_id = data.get('target_pet_id')
    
    pet = current_user.pet
    
    if interaction_type == 'play' and target_pet_id:
        target_pet = Pet.query.get(target_pet_id)
        if target_pet:
            # Both pets get happiness boost
            pet.happiness = min(100, pet.happiness + 10)
            target_pet.happiness = min(100, target_pet.happiness + 10)
            
            emit('pet_play_animation', {
                'pet1': {
                    'id': pet.id,
                    'name': pet.name,
                    'type': pet.pet_type.name,
                    'emoji': pet.pet_type.emoji
                },
                'pet2': {
                    'id': target_pet.id,
                    'name': target_pet.name,
                    'type': target_pet.pet_type.name,
                    'emoji': target_pet.pet_type.emoji
                }
            }, room='playground')
            
            # Award points to both users
            current_user.add_points(5, 'pet_social')
            target_pet.owner.add_points(5, 'pet_social')
    
    elif interaction_type == 'dance':
        pet.happiness = min(100, pet.happiness + 5)
        emit('pet_dance', {
            'pet_id': pet.id,
            'pet_name': pet.name,
            'emoji': pet.pet_type.emoji,
            'owner': current_user.username
        }, room='playground')
        
        current_user.add_points(3, 'pet_entertainment')
    
    db.session.commit()

@socketio.on('share_achievement')
def handle_share_achievement(data):
    """Handle sharing achievements with friends"""
    if not current_user.is_authenticated:
        return
    
    achievement_id = data.get('achievement_id')
    message = data.get('message', '')
    
    # Broadcast achievement to friends (simplified)
    emit('friend_achievement', {
        'username': current_user.username,
        'achievement': achievement_id,
        'message': message,
        'timestamp': datetime.now().strftime('%H:%M'),
        'pet_emoji': current_user.pet.pet_type.emoji if current_user.pet else '🌟'
    }, room='general')  # In production, send only to friends

@social_bp.route('/report_user', methods=['POST'])
@login_required
def report_user():
    """Report inappropriate behavior"""
    data = request.get_json()
    reported_username = data.get('username')
    reason = data.get('reason', '')
    
    if not reported_username:
        return jsonify({'success': False, 'message': 'Username required'})
    
    # In production, store reports in database and notify moderators
    print(f"User {current_user.username} reported {reported_username} for: {reason}")
    
    return jsonify({
        'success': True, 
        'message': 'Thank you for keeping our community safe! 🛡️'
    })

@social_bp.route('/online_friends')
@login_required
def get_online_friends():
    """Get list of online friends"""
    # In production, implement proper friend relationships
    online_users = User.query.filter(
        User.last_active > datetime.utcnow() - timedelta(minutes=10),
        User.id != current_user.id
    ).limit(20).all()
    
    friends_data = []
    for user in online_users:
        friends_data.append({
            'id': user.id,
            'username': user.username,
            'level': user.level,
            'pet_emoji': user.pet.pet_type.emoji if user.pet else '🌟',
            'status': 'online'
        })
    
    return jsonify({'friends': friends_data})

# Error handlers for socket events
@socketio.on_error_default
def default_error_handler(e):
    print(f'Socket.IO error: {e}')
    emit('error', {'message': 'Something went wrong. Please try again! 🔄'})