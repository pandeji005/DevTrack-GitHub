from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from app.models import db, Log, Repository, Commit
from app.services.github_service import GithubService
from datetime import datetime

logs_bp = Blueprint('logs', __name__, url_prefix='/api/logs')

@logs_bp.route('', methods=['POST'])
@login_required
def save_log():
    data = request.get_json()
    content = data.get('content')
    repo_id = session.get('current_repo_id')
    
    if not repo_id:
        return jsonify({'error': 'No repository selected'}), 400
    
    repo = Repository.query.get(repo_id)
    if not repo:
        return jsonify({'error': 'Repository not found'}), 404

    today = datetime.utcnow().date()
    
    # Save to DB
    log = Log.query.filter_by(user_id=current_user.id, repository_id=repo_id, date=today).first()
    if not log:
        log = Log(user_id=current_user.id, repository_id=repo_id, date=today, content=content)
        db.session.add(log)
    else:
        log.content = content
    
    db.session.commit()
    # Commit to GitHub
    try:
        repo_full_name = repo.url.replace('https://github.com/', '').strip('/')
        file_path = f"logs/{today.isoformat()}.md"
        
        # Generate professional commit message
        lines = content.strip().split('\n')
        first_line = lines[0].strip('# ').strip() if lines else ""
        
        # Check if first line looks like a professional title
        if len(first_line) > 5 and len(first_line) < 100:
            commit_message = f"docs(logs): {first_line}"
        else:
            commit_message = f"chore(logs): update dev logs for {today.isoformat()}"
        
        # If user explicitly provided a message in request
        if data.get('commit_message'):
            commit_message = data.get('commit_message')
        
        sha = GithubService.push_commit(
            user=current_user,
            repo_name=repo_full_name,
            file_path=file_path,
            content=content,
            commit_message=commit_message
        )
        
        # Record commit in DB for activity tracking
        new_commit = Commit(
            user_id=current_user.id,
            repository_id=repo_id,
            sha=sha,
            message=commit_message,
            files_changed=file_path
        )
        db.session.add(new_commit)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Log saved and committed to GitHub', 'sha': sha}), 200
    except Exception as e:
        print(f"GitHub Error: {e}")
        return jsonify({
            'success': False, 
            'message': 'Log saved locally, but GitHub commit failed. Please check your repository permissions or branch settings.', 
            'error': str(e)
        }), 500

@logs_bp.route('/today', methods=['GET'])
@login_required
def get_today_log():
    repo_id = session.get('current_repo_id')
    if not repo_id:
        return jsonify({'content': ''})
        
    today = datetime.utcnow().date()
    log = Log.query.filter_by(user_id=current_user.id, repository_id=repo_id, date=today).first()
    return jsonify({'content': log.content if log else ''})
