from datetime import datetime

from app import db


class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    url = db.Column(db.String(200), nullable=False)
    domain = db.Column(db.String(100), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    def __repr__(self):
        return f'<Bookmark {self.url}>'
