from flask_sqlalchemy import SQLAlchemy

# Instantiated here to avoid circular imports between app.py and models.py
db = SQLAlchemy()
