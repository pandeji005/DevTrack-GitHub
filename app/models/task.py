from datetime import datetime
from . import db

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id', ondelete='CASCADE'), nullable=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='todo')   # backlog | todo | in_progress | review | done
    type = db.Column(db.String(20), default='feature')  # feature | bugfix | learning | devops
    priority = db.Column(db.String(10), default='medium')  # low | medium | high | critical
    labels = db.Column(db.Text, nullable=True)          # comma-separated labels
    due_date = db.Column(db.DateTime, nullable=True)
    committed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'repository_id': self.repository_id,
            'title': self.title,
            'description': self.description or '',
            'status': self.status,
            'type': self.type,
            'priority': self.priority,
            'labels': self.labels.split(',') if self.labels else [],
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'committed': self.committed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    def __repr__(self):
        return f'<Task {self.id} - {self.title}>'
