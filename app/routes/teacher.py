from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.lesson import Lesson, Subject, UserLessonProgress
from app.models.achievement import Achievement, UserAchievement
from app.models.pet import Pet
from app.services.llm_service import LLMService
from datetime import datetime, timedelta
import json

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')
llm_service = LLMService()

@teacher_bp.route('/dashboard')
@login_required
def dashboard():
    """Teacher dashboard with student progress overview"""
    # Get all students (in production, filter by teacher's class)
    students = User.query.filter(User.role == 'student').all()
    
    # Calculate overall statistics
    total_students = len(students)
    active_students = len([s for s in students if s.last_active > datetime.utcnow() - timedelta(days=7)])
    avg_level = sum(s.level for s in students) / total_students if total_students > 0 else 0
    
    # Get top performing students
    top_students = sorted(students, key=lambda s: s.total_points, reverse=True)[:10]
    
    # Get lesson completion stats
    lesson_stats = db.session.query(
        Subject.name,
        db.func.count(UserLessonProgress.id).label('completions'),
        db.func.avg(UserLessonProgress.score).label('avg_score')
    ).join(Lesson).join(UserLessonProgress).group_by(Subject.id).all()
    
    return render_template('teacher_dashboard.html',
                         students=students,
                         total_students=total_students,
                         active_students=active_students,
                         avg_level=round(avg_level, 1),
                         top_students=top_students,
                         lesson_stats=lesson_stats)

@teacher_bp.route('/student/<int:student_id>')
@login_required
def student_detail(student_id):
    """Detailed view of individual student progress"""
    student = User.query.get_or_404(student_id)
    
    # Get student's lesson progress
    progress = UserLessonProgress.query.filter_by(user_id=student_id)\
        .join(Lesson).join(Subject).all()
    
    # Group progress by subject
    subject_progress = {}
    for p in progress:
        subject_name = p.lesson.subject.name
        if subject_name not in subject_progress:
            subject_progress[subject_name] = []
        subject_progress[subject_name].append({
            'lesson_title': p.lesson.title,
            'score': p.score,
            'completed_at': p.completed_at,
            'attempts': p.attempts
        })
    
    # Get student's achievements
    achievements = UserAchievement.query.filter_by(user_id=student_id)\
        .join(Achievement).all()
    
    # Get pet information
    pet = Pet.query.filter_by(user_id=student_id).first()
    
    # Calculate learning insights using AI
    insights = generate_student_insights(student, subject_progress)
    
    return render_template('student_detail.html',
                         student=student,
                         subject_progress=subject_progress,
                         achievements=achievements,
                         pet=pet,
                         insights=insights)

@teacher_bp.route('/create_lesson', methods=['GET', 'POST'])
@login_required
def create_lesson():
    """Create a new lesson with AI assistance"""
    if request.method == 'GET':
        subjects = Subject.query.all()
        return render_template('create_lesson.html', subjects=subjects)
    
    data = request.get_json()
    
    # Generate lesson content using AI
    lesson_content = llm_service.generate_lesson_content(
        subject=data.get('subject'),
        topic=data.get('topic'),
        difficulty=data.get('difficulty', 'beginner'),
        age_group=data.get('age_group', '8-12')
    )
    
    # Create lesson in database
    lesson = Lesson(
        title=data.get('title'),
        subject_id=data.get('subject_id'),
        content=lesson_content,
        difficulty=data.get('difficulty', 'beginner'),
        estimated_duration=data.get('duration', 15),
        created_by=current_user.id
    )
    
    db.session.add(lesson)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'lesson_id': lesson.id,
        'message': 'Lesson created successfully! ✨'
    })

@teacher_bp.route('/lesson_analytics/<int:lesson_id>')
@login_required
def lesson_analytics(lesson_id):
    """Analytics for a specific lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Get completion data
    progress_data = UserLessonProgress.query.filter_by(lesson_id=lesson_id).all()
    
    # Calculate statistics
    total_attempts = len(progress_data)
    completed = len([p for p in progress_data if p.completed])
    avg_score = sum(p.score for p in progress_data) / total_attempts if total_attempts > 0 else 0
    avg_time = sum(p.time_spent for p in progress_data if p.time_spent) / total_attempts if total_attempts > 0 else 0
    
    # Group by difficulty/performance
    performance_groups = {
        'struggling': [p for p in progress_data if p.score < 60],
        'average': [p for p in progress_data if 60 <= p.score < 80],
        'excellent': [p for p in progress_data if p.score >= 80]
    }
    
    return render_template('lesson_analytics.html',
                         lesson=lesson,
                         total_attempts=total_attempts,
                         completed=completed,
                         completion_rate=round(completed/total_attempts*100, 1) if total_attempts > 0 else 0,
                         avg_score=round(avg_score, 1),
                         avg_time=round(avg_time, 1),
                         performance_groups=performance_groups)

@teacher_bp.route('/send_encouragement', methods=['POST'])
@login_required
def send_encouragement():
    """Send personalized encouragement to students"""
    data = request.get_json()
    student_id = data.get('student_id')
    message_type = data.get('type', 'general')
    
    student = User.query.get_or_404(student_id)
    
    # Generate personalized encouragement using AI
    encouragement = llm_service.generate_encouragement(
        student_name=student.username,
        recent_activity=get_student_recent_activity(student),
        message_type=message_type
    )
    
    # Store encouragement message (in production, implement proper messaging system)
    student.encouragement_messages = student.encouragement_messages or []
    student.encouragement_messages.append({
        'message': encouragement,
        'from_teacher': current_user.username,
        'timestamp': datetime.utcnow().isoformat(),
        'type': message_type
    })
    
    # Award happiness points to student's pet
    if student.pet:
        student.pet.happiness = min(100, student.pet.happiness + 15)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Encouragement sent! The student will be so happy! 🌟'
    })

@teacher_bp.route('/class_performance')
@login_required
def class_performance():
    """Overall class performance metrics"""
    # Get performance data for charts
    students = User.query.filter(User.role == 'student').all()
    
    # Performance by subject
    subject_performance = {}
    for subject in Subject.query.all():
        avg_score = db.session.query(db.func.avg(UserLessonProgress.score))\
            .join(Lesson).filter(Lesson.subject_id == subject.id).scalar() or 0
        subject_performance[subject.name] = round(avg_score, 1)
    
    # Learning time distribution
    time_distribution = {}
    for student in students:
        total_time = sum(p.time_spent for p in student.lesson_progress if p.time_spent)
        time_range = get_time_range(total_time)
        time_distribution[time_range] = time_distribution.get(time_range, 0) + 1
    
    # Pet happiness correlation with learning
    pet_learning_correlation = []
    for student in students:
        if student.pet:
            avg_score = sum(p.score for p in student.lesson_progress) / len(student.lesson_progress) if student.lesson_progress else 0
            pet_learning_correlation.append({
                'pet_happiness': student.pet.happiness,
                'learning_score': avg_score,
                'student_name': student.username
            })
    
    return render_template('class_performance.html',
                         subject_performance=subject_performance,
                         time_distribution=time_distribution,
                         pet_learning_correlation=pet_learning_correlation)

@teacher_bp.route('/generate_report/<int:student_id>')
@login_required
def generate_report(student_id):
    """Generate comprehensive student report"""
    student = User.query.get_or_404(student_id)
    
    # Collect all relevant data
    progress_data = UserLessonProgress.query.filter_by(user_id=student_id).all()
    achievements = UserAchievement.query.filter_by(user_id=student_id).all()
    
    # Generate AI-powered insights and recommendations
    report_data = {
        'student': student,
        'summary': generate_student_summary(student, progress_data),
        'strengths': identify_strengths(progress_data),
        'areas_for_improvement': identify_improvement_areas(progress_data),
        'recommendations': generate_recommendations(student, progress_data),
        'social_interaction': analyze_social_participation(student),
        'pet_care_responsibility': analyze_pet_care(student),
        'emotional_wellbeing': assess_emotional_state(student)
    }
    
    return render_template('student_report.html', **report_data)

# Helper functions
def generate_student_insights(student, subject_progress):
    """Generate AI-powered insights about student learning"""
    insights = []
    
    # Analyze performance patterns
    if subject_progress:
        best_subject = max(subject_progress.keys(), 
                          key=lambda s: sum(p['score'] for p in subject_progress[s]) / len(subject_progress[s]))
        insights.append(f"🌟 {student.username} excels in {best_subject}!")
        
        # Check for improvement trends
        for subject, progress in subject_progress.items():
            if len(progress) >= 3:
                recent_scores = [p['score'] for p in progress[-3:]]
                if all(recent_scores[i] <= recent_scores[i+1] for i in range(len(recent_scores)-1)):
                    insights.append(f"📈 Great improvement in {subject}!")
    
    # Analyze pet care as responsibility indicator
    if student.pet:
        if student.pet.happiness > 80:
            insights.append("💖 Excellent pet care shows great responsibility!")
        elif student.pet.happiness < 40:
            insights.append("🤗 Pet needs more attention - teaching moment for care!")
    
    return insights

def get_student_recent_activity(student):
    """Get recent activity for personalized messages"""
    recent_progress = UserLessonProgress.query.filter_by(user_id=student.id)\
        .filter(UserLessonProgress.completed_at > datetime.utcnow() - timedelta(days=7))\
        .order_by(UserLessonProgress.completed_at.desc()).limit(5).all()
    
    return [
        {
            'lesson': p.lesson.title,
            'score': p.score,
            'subject': p.lesson.subject.name
        }
        for p in recent_progress
    ]

def get_time_range(total_minutes):
    """Categorize learning time into ranges"""
    if total_minutes < 60:
        return "0-1 hours"
    elif total_minutes < 180:
        return "1-3 hours"
    elif total_minutes < 300:
        return "3-5 hours"
    else:
        return "5+ hours"

def generate_student_summary(student, progress_data):
    """Generate comprehensive student summary"""
    total_lessons = len(progress_data)
    avg_score = sum(p.score for p in progress_data) / total_lessons if total_lessons > 0 else 0
    
    return {
        'total_lessons_completed': total_lessons,
        'average_score': round(avg_score, 1),
        'current_level': student.level,
        'total_points': student.total_points,
        'days_active': (datetime.utcnow() - student.created_at).days,
        'pet_happiness': student.pet.happiness if student.pet else 0
    }

def identify_strengths(progress_data):
    """Identify student's academic strengths"""
    subject_scores = {}
    for progress in progress_data:
        subject = progress.lesson.subject.name
        if subject not in subject_scores:
            subject_scores[subject] = []
        subject_scores[subject].append(progress.score)
    
    strengths = []
    for subject, scores in subject_scores.items():
        avg_score = sum(scores) / len(scores)
        if avg_score >= 85:
            strengths.append(f"Exceptional performance in {subject} ({avg_score:.1f}% average)")
        elif avg_score >= 75:
            strengths.append(f"Strong grasp of {subject} concepts ({avg_score:.1f}% average)")
    
    return strengths

def identify_improvement_areas(progress_data):
    """Identify areas needing improvement"""
    subject_scores = {}
    for progress in progress_data:
        subject = progress.lesson.subject.name
        if subject not in subject_scores:
            subject_scores[subject] = []
        subject_scores[subject].append(progress.score)
    
    improvements = []
    for subject, scores in subject_scores.items():
        avg_score = sum(scores) / len(scores)
        if avg_score < 60:
            improvements.append(f"{subject} needs additional support ({avg_score:.1f}% average)")
        elif avg_score < 70:
            improvements.append(f"{subject} could benefit from extra practice ({avg_score:.1f}% average)")
    
    return improvements

def generate_recommendations(student, progress_data):
    """Generate personalized learning recommendations"""
    recommendations = []
    
    # Based on performance patterns
    if progress_data:
        recent_scores = [p.score for p in progress_data[-5:]]
        if len(recent_scores) >= 3:
            if all(s < 70 for s in recent_scores[-3:]):
                recommendations.append("Consider breaking lessons into smaller chunks")
                recommendations.append("Increase interactive elements and games")
            elif all(s > 85 for s in recent_scores[-3:]):
                recommendations.append("Ready for more challenging content")
                recommendations.append("Could mentor other students")
    
    # Based on pet care
    if student.pet and student.pet.happiness < 50:
        recommendations.append("Encourage more consistent pet care for responsibility building")
    
    return recommendations

def analyze_social_participation(student):
    """Analyze student's social interaction patterns"""
    # In production, track actual social interactions
    return {
        'chat_participation': 'Active',  # Placeholder
        'peer_collaboration': 'Good',
        'friend_count': 5,  # Placeholder
        'positive_interactions': 15  # Placeholder
    }

def analyze_pet_care(student):
    """Analyze pet care patterns for responsibility assessment"""
    if not student.pet:
        return {'has_pet': False}
    
    return {
        'has_pet': True,
        'pet_type': student.pet.pet_type.name,
        'happiness_level': student.pet.happiness,
        'hunger_management': 'Good' if student.pet.hunger < 30 else 'Needs attention',
        'care_consistency': 'Regular'  # In production, track feeding patterns
    }

def assess_emotional_state(student):
    """Assess student's emotional wellbeing indicators"""
    # In production, use actual emotion tracking data
    return {
        'overall_mood': 'Positive',
        'stress_indicators': 'Low',
        'engagement_level': 'High',
        'support_needed': 'None currently'
    }