from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    age           = db.Column(db.Integer)
    gender        = db.Column(db.String(10))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    entries       = db.relationship('HealthEntry', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class HealthEntry(db.Model):
    __tablename__ = 'health_entries'
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    weight           = db.Column(db.Float)           # kg
    systolic_bp      = db.Column(db.Integer)         # mmHg
    diastolic_bp     = db.Column(db.Integer)         # mmHg
    sugar_level      = db.Column(db.Float)           # mg/dL
    sleep_hours      = db.Column(db.Float)           # hours
    exercise_minutes = db.Column(db.Integer)         # minutes
    mood             = db.Column(db.Integer)         # 1-10
    stress_level     = db.Column(db.Integer)         # 1-10
    notes            = db.Column(db.Text)
    timestamp        = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'weight': self.weight,
            'systolic_bp': self.systolic_bp,
            'diastolic_bp': self.diastolic_bp,
            'sugar_level': self.sugar_level,
            'sleep_hours': self.sleep_hours,
            'exercise_minutes': self.exercise_minutes,
            'mood': self.mood,
            'stress_level': self.stress_level,
            'notes': self.notes,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M')
        }

    def __repr__(self):
        return f'<HealthEntry {self.id} by User {self.user_id}>'
