from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Instantiated here to avoid circular imports
db = SQLAlchemy()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id: str):
    from models import User
    return db.session.get(User, int(user_id))
