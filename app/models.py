from datetime import datetime

from flask_login import UserMixin

from app import db, login


class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    url = db.Column(db.String(200), nullable=False)
    domain = db.Column(db.String(100), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    def __repr__(self):
        return f'<Bookmark {self.url}>'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    # other fields as needed

    # User loader
    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))
