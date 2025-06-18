from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, current_user, logout_user, login_required
from app.models.user import User
from app import db
import bcrypt

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password, user.password):
            login_user(user)
            if not user.assessment_completed:
                flash('Welcome! Let’s start with a fun assessment!', 'info')
                return redirect(url_for('assessment_games.knowledge_assessment'))
            return redirect(url_for('pet_companion.pet'))
        flash('Oops! Wrong email or password. Try again!', 'danger')
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        user = User(email=email, username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Log in to meet your pet!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('See you soon! Your pet will miss you!', 'info')
    return redirect(url_for('auth.login'))