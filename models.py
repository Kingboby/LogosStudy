from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    streak = db.Column(db.Integer, default=0)
    last_active = db.Column(db.Date, nullable=True)


class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    file_path = db.Column(db.String(200), nullable=False, unique=True)
    year = db.Column(db.Integer, nullable=True)
