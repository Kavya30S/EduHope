from app.models.lesson import Lesson
from app.models.user import User
from app.config import Config
from sklearn.cluster import KMeans
import numpy as np
import plotly.express as px
import pandas as pd

def predict_learning_style(user_id):
    progress = GameProgress.query.filter_by(user_id=user_id).all()
    if not progress:
        return 'visual'
    scores = np.array([[p.score for p in progress]])
    kmeans = KMeans(n_clusters=3, random_state=0).fit(scores.T)
    style_map = {0: 'visual', 1: 'auditory', 2: 'kinesthetic'}
    return style_map[kmeans.labels_[0]]

def get_personalized_lessons(user_id):
    config = Config()
    dataset_path = config.get_dataset_path('who')  # Corrected to use custom_health_facts.txt
    with open(dataset_path, 'r', encoding='utf-8') as f:
        health_facts = f.readlines()
    user = User.query.get(user_id)
    user.learning_style = predict_learning_style(user_id)
    db.session.commit()
    lessons = Lesson.query.filter_by(difficulty=user.points // 100 + 1).all()
    for i, lesson in enumerate(lessons):
        lesson.health_fact = health_facts[i % len(health_facts)] if health_facts else "No fact"
    return lessons

def generate_progress_chart(user_id):
    progress = GameProgress.query.filter_by(user_id=user_id).all()
    df = pd.DataFrame([(p.game_type, p.score) for p in progress], columns=['Game Type', 'Score'])
    fig = px.bar(df, x='Game Type', y='Score', title='User Progress')
    return fig.to_html()