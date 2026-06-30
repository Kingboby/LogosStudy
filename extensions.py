from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# shared extension instances, so models and app.py can import without a circular import
db = SQLAlchemy()
loginManager = LoginManager()
loginManager.login_view = "fnRouteLogin"
