from datetime import date
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from app.models import db, Task, Log, Commit, Repository
from app.services.github_service import GithubService
from app.services.ai_service import AIService
from app import socketio

commits_bp = Blueprint('commits', __name__)

@commits_bp.route('/repo/create', methods=['POST'])
@login_required
def create_repo():
    data = request.get_json() or {}
    repo_name = data.get('repo_name', 'devtrack-logs')
    
    try:
        repo, created = GithubService.create_repo(current_user, repo_name)
        
        current_user.repo_name = repo.name
        current_user.repo_url = repo.html_url
        db.session.commit()
        
        return jsonify({
            'message': 'Repository ready',
            'repo_name': repo.name,
            'repo_url': repo.html_url,
            'created': created
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@commits_bp.route('/api/commit', methods=['POST'])
@login_required
def push_commit():
    repo_id = session.get('current_repo_id')
    if not repo_id:
        return jsonify({'error': 'No workspace selected.'}), 400
        
    repo = Repository.query.filter_by(id=repo_id, user_id=current_user.id).first()
    if not repo or not repo.name:
        return jsonify({'error': 'Repository not linked. Please create the repo first.'}), 400
        
    today = date.today()
    
    # 1. Fetch uncommitted done tasks + today's log
    tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.repository_id == repo_id,
        Task.status == 'done',
        Task.committed == False
    ).all()
    
    log = Log.query.filter_by(user_id=current_user.id, repository_id=repo_id, date=today).first()
    
    if not tasks and (not log or not log.content.strip()):
        return jsonify({'error': 'Nothing to commit today.'}), 400
        
    # 2. Format content
    file_path = f"logs/{today.isoformat()}.md"
    content = f"# Log for {today.isoformat()}\n\n"
    
    log_content = ""
    if log and log.content:
        log_content = log.content
        content += f"## Daily Notes\n{log_content}\n\n"
        
    if tasks:
        content += "## Completed Tasks\n"
        for t in tasks:
            content += f"- [{t.type}] {t.title} ({t.priority})\n"
            
    # 3. Message using Groq AI
    try:
        commit_message = AIService.generate_smart_commit(tasks, log_content)
    except Exception as e:
        print(f"AI Commit generation failed: {e}")
        commit_message = f"chore(logs): update dev logs for {today.isoformat()}"
    
    try:
        # 4. Push to GitHub
        sha = GithubService.push_commit(
            current_user,
            repo.name,
            file_path,
            content,
            commit_message
        )
        
        # 5. Store in DB
        commit_record = Commit(
            user_id=current_user.id,
            repository_id=repo_id,
            sha=sha,
            message=commit_message,
            files_changed=file_path
        )
        db.session.add(commit_record)
        
        # Mark tasks as committed
        for t in tasks:
            t.committed = True
            
        db.session.commit()
        
        # Update Streak
        from app.services.streak_service import StreakService
        streak = StreakService.update_streak(current_user.id)
        
        # 6. Emit event
        socketio.emit('commit:pushed', {
            'sha': sha,
            'message': commit_message,
            'date': today.isoformat(),
            'streak': streak.current_streak
        }, to=f"user_{current_user.id}")
        
        return jsonify({'message': 'Committed successfully', 'sha': sha})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
