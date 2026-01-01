from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
from datetime import datetime, timezone, timedelta

# Define IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def current_ist():
    return datetime.now(IST)

def current_utc():
    return datetime.utcnow()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # 'admin' or 'user'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Hall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bid = db.Column(db.String(6), unique=True, nullable=False)
    hall_id = db.Column(db.Integer, db.ForeignKey('hall.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(10), nullable=False)  # 'day' or 'night'
    client_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'confirmed' or 'pending'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=current_utc)
    confirmed_at = db.Column(db.DateTime, nullable=True)

    hall = db.relationship('Hall', backref=db.backref('bookings', lazy=True))
    user = db.relationship('User', backref=db.backref('bookings', lazy=True))

    @staticmethod
    def generate_bid():
        while True:
            bid = ''.join(random.choices(string.digits, k=6))
            if not Booking.query.filter_by(bid=bid).first():
                return bid