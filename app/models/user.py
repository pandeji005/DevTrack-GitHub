from datetime import datetime
from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    github_id = db.Column(db.Integer, unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    avatar_url = db.Column(db.Text)
    access_token = db.Column(db.Text)  # Encrypted at rest
    bio = db.Column(db.String(255))
    twitter_handle = db.Column(db.String(100))
    website = db.Column(db.String(200))
    repositories = db.relationship('Repository', back_populates='user', cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def __repr__(self):
        return f'<User {self.username}>'
