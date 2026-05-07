from . import db

class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id', ondelete='CASCADE'), nullable=True)
    date = db.Column(db.Date, nullable=False)
    content = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'repository_id', 'date', name='uq_user_repo_date'),
    )

    def __init__(self, **kwargs):
        super(Log, self).__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat(),
            'content': self.content,
            'is_public': self.is_public
        }

    def __repr__(self):
        return f'<Log {self.user_id} - {self.date}>'
