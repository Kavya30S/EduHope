from app import db

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(20), default='Buddy')  # Customizable pet name
    type = db.Column(db.String(20), nullable=False)  # e.g., 'dragon', 'unicorn'
    hunger = db.Column(db.Integer, default=50)  # 0-100 scale
    happiness = db.Column(db.Integer, default=50)  # 0-100 scale
    knowledge = db.Column(db.Integer, default=0)  # Grows with learning activities
    level = db.Column(db.Integer, default=1)  # Levels up every 100 knowledge points