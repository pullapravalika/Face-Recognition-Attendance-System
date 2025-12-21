# models.py
from . import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import PickleType
from app import db
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'student'
    photo_filename = db.Column(db.String(100), nullable=False)
    # Admin specific fields
    cid = db.Column(db.String(50))
    branch = db.Column(db.String(50))
    year = db.Column(db.String(10))
    photo_filename = db.Column(db.String(200))
    # Student specific fields
    father_name = db.Column(db.String(100))
    student_id = db.Column(db.String(50))
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    face_encoding = db.Column(PickleType, nullable=True)  # New column to store encoding
class ClassSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(10), nullable=False)
    subject = db.Column(db.String(100))
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(10), nullable=False)
    attendances = db.relationship('Attendance', back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    def __repr__(self):
       return f"<ClassSession {self.day} {self.start_time}-{self.end_time} ({self.branch} {self.year})>"

class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_session_id = db.Column(db.Integer, db.ForeignKey('class_session.id', ondelete='CASCADE'), nullable=False)
    present = db.Column(db.Boolean, nullable=False)
    presence_seconds = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    present_minutes = db.Column(db.Float)
    session = db.relationship('ClassSession', back_populates="attendances")
