from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
loginManager = LoginManager()
loginManager.login_view = "fnRouteLogin"
