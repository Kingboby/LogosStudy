from datetime import datetime
from zoneinfo import ZoneInfo
from flask_login import UserMixin
from extensions import db

#set all time, sydney time for HSC students
SYDNEY_TZ = ZoneInfo("Australia/Sydney")

def fnNowSydney():
    return datetime.now(SYDNEY_TZ).replace(tzinfo=None)

# creates database table for registered accounts - flask-login expects
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False) # werkzeug hashed, not plain text
    streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_active = db.Column(db.Date, nullable=True) # last day a session was saved
    calendar_url = db.Column(db.String(500), nullable=True) # linked .ics feed

# creates  table for todolist items, each associated with a user id.
class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    is_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=fnNowSydney)

# created table for study session, logged when timer finishes
class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    session_type = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, default=fnNowSydney)
