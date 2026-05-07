from datetime import datetime
from . import db

class Repository(db.Model):
    __tablename__ = 'repositories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.Text)
    language = db.Column(db.String(100), nullable=True)
    visibility = db.Column(db.String(50), default='public')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='repositories')
    tasks = db.relationship('Task', backref='repository', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        from app.models.task import Task
        from app.models.commit import Commit
        task_count = Task.query.filter_by(repository_id=self.id).filter(Task.status != 'done').count()
        commit_count = Commit.query.filter_by(repository_id=self.id).count()
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'url': self.url or '',
            'language': self.language or '',
            'visibility': self.visibility,
            'active_task_count': task_count,
            'commit_count': commit_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    def __init__(self, **kwargs):
        super(Repository, self).__init__(**kwargs)

    def __repr__(self):
        return f'<Repository {self.name}>'
