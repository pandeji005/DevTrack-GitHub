from . import db

class Streak(db.Model):
    __tablename__ = 'streaks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_commit_date = db.Column(db.Date, nullable=True)
    total_commits = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'last_commit_date': self.last_commit_date.isoformat() if self.last_commit_date else None,
            'total_commits': self.total_commits
        }
