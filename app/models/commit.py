from datetime import datetime
from . import db

class Commit(db.Model):
    __tablename__ = 'commits'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id', ondelete='CASCADE'), nullable=True)
    sha = db.Column(db.String(40))
    message = db.Column(db.Text)
    files_changed = db.Column(db.Text) # Storing as comma-separated string for SQLite compatibility
    committed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sha': self.sha,
            'message': self.message,
            'files_changed': self.files_changed.split(',') if self.files_changed else [],
            'committed_at': self.committed_at.isoformat() if self.committed_at else None
        }
    def __init__(self, **kwargs):
        super(Commit, self).__init__(**kwargs)

    def __repr__(self):
        return f'<Commit {self.sha}>'
