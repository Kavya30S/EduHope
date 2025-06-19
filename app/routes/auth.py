from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app.models.pet import Pet
from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement
from app import db
import re

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            session.permanent = True
            
            # Award first login achievement
            first_login_ach = Achievement.query.filter_by(name='First Login').first()
            if first_login_ach and not UserAchievement.query.filter_by(
                user_id=user.id, achievement_id=first_login_ach.id
            ).first():
                user_ach = UserAchievement(user_id=user.id, achievement_id=first_login_ach.id)
                db.session.add(user_ach)
                user.total_points += first_login_ach.points
                db.session.commit()
                flash(f'Achievement unlocked: {first_login_ach.name}! +{first_login_ach.points} points', 'achievement')
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard.index')
            return redirect(next_page)
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        age = request.form.get('age', type=int)
        language = request.form.get('language', 'en')
        pet_type = request.form.get('pet_type', 'dragon')
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('Username can only contain letters, numbers, and underscores.')
        elif User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        
        if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors.append('Please enter a valid email address.')
        elif User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        elif password != confirm_password:
            errors.append('Passwords do not match.')
        
        if not age or age < 5 or age > 18:
            errors.append('Age must be between 5 and 18.')
        
        if not pet_type or pet_type not in ['dragon', 'unicorn', 'robot', 'phoenix', 'tiger']:
            errors.append('Please select a valid pet type.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html', 
                                 username=username, email=email, age=age, 
                                 language=language, pet_type=pet_type)
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            age=age,
            language=language,
            total_points=0,
            level=1
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create pet
        pet = Pet(
            user_id=user.id,
            name=f"{username}'s {pet_type.title()}",
            pet_type=pet_type,
            level=1,
            experience=0,
            happiness=80,
            hunger=70,
            health=100,
            energy=90
        )
        
        db.session.add(pet)
        
        # Award pet owner achievement
        pet_owner_ach = Achievement.query.filter_by(name='Pet Owner').first()
        if pet_owner_ach:
            user_ach = UserAchievement(user_id=user.id, achievement_id=pet_owner_ach.id)
            db.session.add(user_ach)
            user.total_points += pet_owner_ach.points
        
        db.session.commit()
        
        flash(f'Welcome to EduHope, {username}! Your {pet_type} is ready to learn with you!', 'success')
        login_user(user)
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/profile')
@login_required
def profile():
    user_achievements = db.session.query(UserAchievement, Achievement).join(
        Achievement, UserAchievement.achievement_id == Achievement.id
    ).filter(UserAchievement.user_id == current_user.id).all()
    
    return render_template('auth/profile.html', achievements=user_achievements)

@auth.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    email = request.form.get('email', '').strip()
    language = request.form.get('language', 'en')
    
    if email and re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        existing_user = User.query.filter_by(email=email).first()
        if not existing_user or existing_user.id == current_user.id:
            current_user.email = email
            current_user.language = language
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        else:
            flash('Email already registered to another user.', 'error')
    else:
        flash('Please enter a valid email address.', 'error')
    
    return redirect(url_for('auth.profile'))

@auth.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect.', 'error')
    elif len(new_password) < 6:
        flash('New password must be at least 6 characters long.', 'error')
    elif new_password != confirm_password:
        flash('New passwords do not match.', 'error')
    else:
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
    
    return redirect(url_for('auth.profile'))

@auth.route('/check_username')
def check_username():
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'available': False, 'message': 'Username is required'})
    
    if len(username) < 3:
        return jsonify({'available': False, 'message': 'Username must be at least 3 characters long'})
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return jsonify({'available': False, 'message': 'Username can only contain letters, numbers, and underscores'})
    
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'available': False, 'message': 'Username already exists'})
    
    return jsonify({'available': True, 'message': 'Username is available'})