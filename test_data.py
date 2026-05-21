# test_data.py
from app import app
from extensions import db
from models import StudySession
from datetime import datetime, timedelta
import random

with app.app_context():
    vToday = datetime.today()
    for vDaysAgo in range(200):
        if random.random() > 0.4:
            vNumSessions = random.randint(1, 4)
            for _ in range(vNumSessions):
                db.session.add(StudySession(
                    user_id=1,
                    duration=1500,
                    session_type="Pomodoro",
                    date=vToday - timedelta(days=vDaysAgo)
                ))
    db.session.commit()
    print("Done")
