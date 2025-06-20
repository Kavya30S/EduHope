from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from app import db, socketio
from app.models.user import User
from app.models.story import Story, StoryContribution, StoryVote
from app.services.llm_service import LLMService
from app.services.moderation_service import ModerationService
from datetime import datetime, timedelta
import json
import random

storytelling_bp = Blueprint('storytelling', __name__, url_prefix='/storytelling')
llm_service = LLMService()
moderation = ModerationService()

# Active storytelling sessions
active_stories = {}

@storytelling_bp.route('/')
@login_required
def storytelling_home():
    """Main storytelling interface"""
    # Get active stories user can join
    active_story_list = Story.query.filter(
        Story.status == 'active',
        Story.max_contributors > Story.current_contributors
    ).order_by(Story.created_at.desc()).limit(10).all()
    
    # Get completed stories for inspiration
    completed_stories = Story.query.filter(
        Story.status == 'completed'
    ).order_by(Story.votes.desc()).limit(5).all()
    
    # Get user's stories
    user_stories = Story.query.filter_by(created_by=current_user.id).all()
    
    return render_template('storytelling.html',
                         active_stories=active_story_list,
                         completed_stories=completed_stories,
                         user_stories=user_stories)

@storytelling_bp.route('/create_story', methods=['POST'])
@login_required
def create_story():
    """Create a new collaborative story"""
    data = request.get_json()
    
    title = data.get('title', '').strip()
    theme = data.get('theme', 'adventure')
    max_contributors = min(int(data.get('max_contributors', 5)), 10)  # Max 10 contributors
    
    if not title:
        return jsonify({'success': False, 'message': 'Story title is required!'})
    
    # Generate story starter using AI
    story_starter = llm_service.generate_story_starter(
        title=title,
        theme=theme,
        age_appropriate=True
    )
    
    # Create story in database
    story = Story(
        title=title,
        theme=theme,
        content=story_starter,
        created_by=current_user.id,
        max_contributors=max_contributors,
        current_contributors=1,
        status='active'
    )
    
    db.session.add(story)
    db.session.commit()
    
    # Add creator as first contributor
    contribution = StoryContribution(
        story_id=story.id,
        user_id=current_user.id,
        content=story_starter,
        order=1
    )
    
    db.session.add(contribution)
    db.session.commit()
    
    # Award points for creativity
    current_user.add_points(10, 'story_creation')
    db.session.commit()
    
    return jsonify({
        'success': True,
        'story_id': story.id,
        'message': 'Story created! Let the magic begin! ✨'
    })

@storytelling_bp.route('/join_story/<int:story_id>')
@login_required
def join_story(story_id):
    """Join an active story"""
    story = Story.query.get_or_404(story_id)
    
    if story.status != 'active':
        return jsonify({'success': False, 'message': 'This story is no longer active'})
    
    if story.current_contributors >= story.max_contributors:
        return jsonify({'success': False, 'message': 'This story is full!'})
    
    # Check if user already contributed
    existing_contribution = StoryContribution.query.filter_by(
        story_id=story_id,
        user_id=current_user.id
    ).first()
    
    if existing_contribution:
        return jsonify({'success': False, 'message': 'You already contributed to this story!'})
    
    return render_template('story_session.html', story=story)

@storytelling_bp.route('/story/<int:story_id>')
@login_required
def view_story(story_id):
    """View a complete story"""
    story = Story.query.get_or_404(story_id)
    contributions = StoryContribution.query.filter_by(story_id=story_id)\
        .order_by(StoryContribution.order).all()
    
    return render_template('view_story.html', story=story, contributions=contributions)

@storytelling_bp.route('/add_contribution', methods=['POST'])
@login_required
def add_contribution():
    """Add a contribution to an active story"""
    data = request.get_json()
    story_id = data.get('story_id')
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'success': False, 'message': 'Please write something!'})
    
    # Moderate content
    if not moderation.is_safe_content(content):
        return jsonify({
            'success': False, 
            'message': 'Please keep your story appropriate for everyone! 🌈'
        })
    
    story = Story.query.get_or_404(story_id)
    
    if story.status != 'active':
        return jsonify({'success': False, 'message': 'This story is complete!'})
    
    # Check if user already contributed
    existing = StoryContribution.query.filter_by(
        story_id=story_id,
        user_id=current_user.id
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': 'You already contributed!'})
    
    # Get AI suggestion for story continuation
    previous_content = ' '.join([c.content for c in story.contributions])
    ai_suggestion = llm_service.get_story_suggestion(previous_content + ' ' + content)
    
    # Add contribution
    next_order = StoryContribution.query.filter_by(story_id=story_id).count() + 1
    contribution = StoryContribution(
        story_id=story_id,
        user_id=current_user.id,
        content=content,
        order=next_order
    )
    
    db.session.add(contribution)
    
    # Update story
    story.current_contributors += 1
    story.content += '\n\n' + content
    story.last_updated = datetime.utcnow()
    
    # Check if story should be completed
    if story.current_contributors >= story.max_contributors:
        story.status = 'completed'
        # Generate AI conclusion
        conclusion = llm_service.generate_story_conclusion(story.content)
        story.content += '\n\n' + conclusion
    
    db.session.commit()
    
    # Award points
    current_user.add_points(8, 'story_contribution')
    db.session.commit()
    
    # Broadcast to other users in the story session
    socketio.emit('new_contribution', {
        'story_id': story_id,
        'username': current_user.username,
        'content': content,
        'pet_emoji': current_user.pet.pet_type.emoji if current_user.pet else '📝',
        'user_level': current_user.level,
        'ai_suggestion': ai_suggestion,
        'story_completed': story.status == 'completed'
    }, room=f'story_{story_id}')
    
    return jsonify({
        'success': True,
        'message': 'Your contribution was added! 🌟',
        'ai_suggestion': ai_suggestion,
        'story_completed': story.status == 'completed'
    })

@storytelling_bp.route('/vote_story', methods=['POST'])
@login_required
def vote_story():
    """Vote for a completed story"""
    data = request.get_json()
    story_id = data.get('story_id')
    vote_type = data.get('vote_type')  # 'like' or 'love'
    
    story = Story.query.get_or_404(story_id)
    
    if story.status != 'completed':
        return jsonify({'success': False, 'message': 'Can only vote on completed stories'})
    
    # Check if user already voted
    existing_vote = StoryVote.query.filter_by(
        story_id=story_id,
        user_id=current_user.id
    ).first()
    
    if existing_vote:
        # Update existing vote
        existing_vote.vote_type = vote_type
    else:
        # Create new vote
        vote = StoryVote(
            story_id=story_id,
            user_id=current_user.id,
            vote_type=vote_type
        )
        db.session.add(vote)
    
    # Update story vote count
    story.votes = StoryVote.query.filter_by(story_id=story_id).count()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Thanks for voting! 💖',
        'total_votes': story.votes
    })

@storytelling_bp.route('/story_prompts')
@login_required
def get_story_prompts():
    """Get AI-generated story prompts for inspiration"""
    prompts = []
    
    themes = ['adventure', 'friendship', 'magic', 'animals', 'space', 'underwater', 'fairy_tale']
    
    for theme in random.sample(themes, 3):
        prompt = llm_service.generate_story_prompt(theme)
        prompts.append({
            'theme': theme,
            'prompt': prompt,
            'emoji': get_theme_emoji(theme)
        })
    
    return jsonify({'prompts': prompts})

@storytelling_bp.route('/my_stories')
@login_required
def my_stories():
    """Get user's story contributions and created stories"""
    created_stories = Story.query.filter_by(created_by=current_user.id).all()
    
    contributed_stories = db.session.query(Story).join(StoryContribution)\
        .filter(StoryContribution.user_id == current_user.id,
                Story.created_by != current_user.id).all()
    
    return render_template('my_stories.html',
                         created_stories=created_stories,
                         contributed_stories=contributed_stories)

# Socket.IO events for real-time storytelling
@socketio.on('join_story_session')
def handle_join_story_session(data):
    """Handle user joining a story session"""
    story_id = data.get('story_id')
    username = current_user.username if current_user.is_authenticated else 'Anonymous'
    
    room = f'story_{story_id}'
    join_room(room)
    
    emit('user_joined_story', {
        'username': username,
        'message': f'{username} joined the storytelling session! ✨',
        'pet_emoji': current_user.pet.pet_type.emoji if current_user.pet else '📚'
    }, room=room)

@socketio.on('leave_story_session')
def handle_leave_story_session(data):
    """Handle user leaving a story session"""
    story_id = data.get('story_id')
    username = current_user.username if current_user.is_authenticated else 'Anonymous'
    
    room = f'story_{story_id}'
    leave_room(room)
    
    emit('user_left_story', {
        'username': username,
        'message': f'{username} left the session. Happy writing! 👋'
    }, room=room)

@socketio.on('typing_story')
def handle_typing_story(data):
    """Handle user typing in story session"""
    story_id = data.get('story_id')
    is_typing = data.get('is_typing', False)
    
    if not current_user.is_authenticated:
        return
    
    room = f'story_{story_id}'
    emit('user_typing_story', {
        'username': current_user.username,
        'is_typing': is_typing
    }, room=room, include_self=False)

@socketio.on('request_ai_help')
def handle_ai_help_request(data):
    """Handle request for AI writing assistance"""
    story_id = data.get('story_id')
    current_text = data.get('current_text', '')
    
    if not current_user.is_authenticated:
        return
    
    # Get story context
    story = Story.query.get(story_id)
    if not story:
        return
    
    # Generate AI suggestions
    suggestions = llm_service.get_writing_suggestions(
        story_context=story.content,
        current_text=current_text
    )
    
    emit('ai_suggestions', {
        'suggestions': suggestions,
        'story_id': story_id
    })

# Helper functions
def get_theme_emoji(theme):
    """Get emoji for story theme"""
    theme_emojis = {
        'adventure': '🏔️',
        'friendship': '👫',
        'magic': '✨',
        'animals': '🐾',
        'space': '🚀',
        'underwater': '🌊',
        'fairy_tale': '🏰'
    }
    return theme_emojis.get(theme, '📖')

@storytelling_bp.route('/hall_of_fame')
@login_required
def hall_of_fame():
    """Display the most popular stories"""
    top_stories = Story.query.filter(Story.status == 'completed')\
        .order_by(Story.votes.desc()).limit(20).all()
    
    return render_template('story_hall_of_fame.html', stories=top_stories)

@storytelling_bp.route('/export_story/<int:story_id>')
@login_required
def export_story(story_id):
    """Export story as a formatted document"""
    story = Story.query.get_or_404(story_id)
    contributions = StoryContribution.query.filter_by(story_id=story_id)\
        .order_by(StoryContribution.order).all()
    
    # Format story for export
    formatted_story = {
        'title': story.title,
        'theme': story.theme,
        'created_at': story.created_at.strftime('%Y-%m-%d'),
        'contributors': [c.user.username for c in contributions],
        'content': story.content,
        'votes': story.votes
    }
    
    return jsonify(formatted_story)