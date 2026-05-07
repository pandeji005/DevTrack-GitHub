from datetime import date, datetime, timedelta
from flask import Blueprint, jsonify, session, request
from flask_login import login_required, current_user
from app.models import db, Commit, Repository
from app.services.github_service import GithubService
from app.services.streak_service import StreakService

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/streaks', methods=['GET'])
@login_required
def get_streaks():
    streak = StreakService.get_or_create(current_user.id)
    # If the user hasn't committed today or yesterday, streak is technically broken
    # but we don't update DB until they commit. We can just return 0 for display
    # if days_diff > 1.
    
    display_streak = streak.current_streak
    if streak.last_commit_date:
        days_diff = (date.today() - streak.last_commit_date).days
        if days_diff > 1:
            display_streak = 0
            
    data = streak.to_dict()
    data['current_streak'] = display_streak
    
    return jsonify(data)

@analytics_bp.route('/heatmap', methods=['GET'])
@login_required
def get_heatmap():
    # Return count of activity per day for the last 365 days
    from datetime import datetime, date
    from app.models import Task, Log
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    
    # 1. Commits
    commits = Commit.query.filter(
        Commit.user_id == current_user.id,
        Commit.committed_at >= one_year_ago
    ).all()
    
    # 2. Tasks Completed
    tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.status == 'done',
        Task.completed_at >= one_year_ago
    ).all()
    
    # 3. Logs Written
    from app.models import Log as LogModel
    logs = LogModel.query.filter(
        LogModel.user_id == current_user.id,
        LogModel.date >= one_year_ago.date()
    ).all()
    
    heatmap = {}
    
    for c in commits:
        d = c.committed_at.date().isoformat()
        heatmap[d] = heatmap.get(d, 0) + 1
        
    for t in tasks:
        d = t.completed_at.date().isoformat()
        heatmap[d] = heatmap.get(d, 0) + 1
        
    for l in logs:
        d = l.date.isoformat()
        heatmap[d] = heatmap.get(d, 0) + 1
    
    # Build full analytics payload
    streak = StreakService.get_or_create(current_user.id)
    display_streak = streak.current_streak
    if streak.last_commit_date:
        days_diff = (date.today() - streak.last_commit_date).days
        if days_diff > 1:
            display_streak = 0

    return jsonify({
        'heatmap': heatmap,
        'total_commits': len(commits),
        'current_streak': display_streak,
        'max_streak': streak.max_streak if hasattr(streak, 'max_streak') else display_streak,
    })

@analytics_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Detailed analytics stats for the Analytics page."""
    from datetime import datetime
    from app.models import Task, Log
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    total_commits = Commit.query.filter(Commit.user_id == current_user.id).count()
    commits_30d = Commit.query.filter(Commit.user_id == current_user.id, Commit.committed_at >= thirty_days_ago).count()
    commits_7d = Commit.query.filter(Commit.user_id == current_user.id, Commit.committed_at >= seven_days_ago).count()

    total_tasks_done = Task.query.filter(Task.user_id == current_user.id, Task.status == 'done').count()
    tasks_done_30d = Task.query.filter(Task.user_id == current_user.id, Task.status == 'done', Task.completed_at >= thirty_days_ago).count()

    streak = StreakService.get_or_create(current_user.id)
    display_streak = streak.current_streak
    if streak.last_commit_date:
        days_diff = (date.today() - streak.last_commit_date).days
        if days_diff > 1:
            display_streak = 0

    # Daily commit counts for last 30 days chart
    daily = {}
    commits_recent = Commit.query.filter(Commit.user_id == current_user.id, Commit.committed_at >= thirty_days_ago).all()
    for c in commits_recent:
        d = c.committed_at.date().isoformat()
        daily[d] = daily.get(d, 0) + 1

    return jsonify({
        'total_commits': total_commits,
        'commits_30d': commits_30d,
        'commits_7d': commits_7d,
        'total_tasks_done': total_tasks_done,
        'tasks_done_30d': tasks_done_30d,
        'current_streak': display_streak,
        'max_streak': getattr(streak, 'max_streak', display_streak),
        'daily_commits': daily,
    })

@analytics_bp.route('/activity', methods=['GET'])
@login_required
def get_activity():
    """Recent activity feed: commits, tasks, logs."""
    from datetime import datetime
    from app.models import Task, Log as LogModel
    repo_id = session.get('current_repo_id')
    limit = int(request.args.get('limit', 30))
    
    events = []
    
    commit_query = Commit.query.filter_by(user_id=current_user.id)
    if repo_id:
        commit_query = commit_query.filter_by(repository_id=repo_id)
    
    commits = commit_query.order_by(Commit.committed_at.desc()).limit(limit).all()
    for c in commits:
        events.append({
            'type': 'commit',
            'title': c.message,
            'meta': c.sha[:7] if c.sha else '',
            'timestamp': c.committed_at.isoformat() if c.committed_at else None,
            'repository_id': c.repository_id,
        })

    task_query = Task.query.filter(Task.user_id == current_user.id, Task.status == 'done', Task.completed_at != None)
    if repo_id:
        task_query = task_query.filter_by(repository_id=repo_id)
        
    tasks = task_query.order_by(Task.completed_at.desc()).limit(limit).all()
    for t in tasks:
        events.append({
            'type': 'task',
            'title': t.title,
            'meta': t.type,
            'timestamp': t.completed_at.isoformat() if t.completed_at else None,
            'repository_id': t.repository_id,
        })

    log_query = LogModel.query.filter_by(user_id=current_user.id)
    if repo_id:
        log_query = log_query.filter_by(repository_id=repo_id)
        
    logs = log_query.order_by(LogModel.date.desc()).limit(limit).all()
    for l in logs:
        # Convert date to datetime for ISO format with time
        dt = datetime.combine(l.date, datetime.min.time())
        events.append({
            'type': 'note',
            'title': f"Daily Log: {l.date}",
            'meta': 'GitHub Synced',
            'timestamp': dt.isoformat(),
            'repository_id': l.repository_id,
        })

    events.sort(key=lambda x: x['timestamp'] or '', reverse=True)
    return jsonify(events[:limit])

@analytics_bp.route('/sync-github', methods=['POST'])
@login_required
def sync_github():
    repo_id = session.get('current_repo_id')
    if not repo_id:
        return jsonify({'error': 'No repository selected'}), 400
        
    repo = Repository.query.get(repo_id)
    if not repo:
        return jsonify({'error': 'Repository not found'}), 404
        
    repo_full_name = repo.url.replace('https://github.com/', '').strip('/').replace('.git', '')
    
    try:
        external_commits = GithubService.get_recent_commits(current_user, repo_full_name)
        new_count = 0
        
        for ec in external_commits:
            # Check if commit already exists
            existing = Commit.query.filter_by(sha=ec['sha']).first()
            if not existing:
                new_commit = Commit(
                    user_id=current_user.id,
                    repository_id=repo_id,
                    sha=ec['sha'],
                    message=ec['message'],
                    committed_at=ec['committed_at']
                )
                db.session.add(new_commit)
                new_count += 1
        
        if new_count > 0:
            db.session.commit()
            
        return jsonify({'success': True, 'new_commits': new_count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
