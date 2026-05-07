from datetime import date, timedelta
from app.models import db, Streak

class StreakService:
    @staticmethod
    def get_or_create(user_id):
        streak = Streak.query.filter_by(user_id=user_id).first()
        if not streak:
            streak = Streak(user_id=user_id)
            db.session.add(streak)
            db.session.commit()
        return streak

    @staticmethod
    def update_streak(user_id):
        streak = StreakService.get_or_create(user_id)
        today = date.today()
        
        # If it's the first commit ever
        if not streak.last_commit_date:
            streak.current_streak = 1
            streak.longest_streak = 1
            streak.last_commit_date = today
            streak.total_commits += 1
            db.session.commit()
            return streak
            
        days_diff = (today - streak.last_commit_date).days
        
        if days_diff == 1:
            # Consecutive day
            streak.current_streak += 1
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
            streak.last_commit_date = today
        elif days_diff > 1:
            # Streak broken
            streak.current_streak = 1
            streak.last_commit_date = today
            
        # If days_diff == 0, it means multiple commits today, streak stays the same
        
        streak.total_commits += 1
        db.session.commit()
        
        return streak
