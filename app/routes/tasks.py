from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from app.models import db, Task, Repository, Commit
from app.services.github_service import GithubService
from datetime import datetime
import json

tasks_bp = Blueprint('tasks_api', __name__, url_prefix='/api/tasks')

def auto_cleanup_tasks(repo_id):
    """Delete tasks that have been 'done' for more than 1 hour and sync to GitHub."""
    from datetime import timedelta
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    
    expired_tasks = Task.query.filter(
        Task.repository_id == repo_id,
        Task.status == 'done',
        Task.completed_at <= one_hour_ago
    ).all()
    
    if not expired_tasks:
        return False

    for task in expired_tasks:
        db.session.delete(task)
    
    db.session.commit()
    
    # Trigger a sync after deletion
    try:
        repo = Repository.query.get(repo_id)
        repo_full_name = repo.url.replace('https://github.com/', '')
        all_tasks = Task.query.filter_by(repository_id=repo_id).all()
        tasks_json = json.dumps([t.to_dict() for t in all_tasks], indent=2)
        
        GithubService.push_commit(
            user=current_user,
            repo_name=repo_full_name,
            file_path=".devtrack/tasks.json",
            content=tasks_json,
            commit_message="Auto-cleanup completed tasks (1h+ old)"
        )
    except Exception as e:
        print(f"Cleanup Sync Error: {e}")
    
    return True

@tasks_bp.route('', methods=['GET'])
@login_required
def get_tasks():
    repo_id = session.get('current_repo_id')
    if not repo_id:
        return jsonify([])
    
    # Run lazy cleanup
    auto_cleanup_tasks(repo_id)
    
    tasks = Task.query.filter_by(user_id=current_user.id, repository_id=repo_id).order_by(Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks])

@tasks_bp.route('', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()
    repo_id = session.get('current_repo_id')
    
    if not repo_id:
        return jsonify({'error': 'No repository selected'}), 400
    
    repo = Repository.query.get(repo_id)
    
    new_task = Task(
        user_id=current_user.id,
        repository_id=repo_id,
        title=data.get('title'),
        description=data.get('description'),
        status=data.get('status', 'todo'),
        priority=data.get('priority', 'medium'),
        type=data.get('type', 'feature')
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    # Sync all tasks for this repo to GitHub in a JSON file
    try:
        repo_full_name = repo.url.replace('https://github.com/', '')
        all_tasks = Task.query.filter_by(user_id=current_user.id, repository_id=repo_id).all()
        tasks_json = json.dumps([t.to_dict() for t in all_tasks], indent=2)
        
        sha = GithubService.push_commit(
            user=current_user,
            repo_name=repo_full_name,
            file_path=".devtrack/tasks.json",
            content=tasks_json,
            commit_message=f"Sync tasks: {new_task.title}"
        )
        
        # Record commit in DB for activity tracking
        new_commit = Commit(
            user_id=current_user.id,
            repository_id=repo_id,
            sha=sha,
            message=f"Sync tasks: {new_task.title}",
            files_changed=".devtrack/tasks.json"
        )
        db.session.add(new_commit)
        new_task.committed = True
        db.session.commit()
    except Exception as e:
        print(f"GitHub Error: {e}")
        return jsonify({
            'success': False,
            'message': 'Task created locally, but GitHub sync failed.',
            'error': str(e),
            'task': new_task.to_dict()
        }), 500

    return jsonify(new_task.to_dict()), 201

@tasks_bp.route('/<int:task_id>', methods=['PATCH'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    if 'status' in data:
        task.status = data['status']
        if task.status == 'done' and not task.completed_at:
            task.completed_at = datetime.utcnow()
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'priority' in data:
        task.priority = data['priority']
        
    db.session.commit()
    
    # Sync to GitHub
    try:
        repo = Repository.query.get(task.repository_id)
        repo_full_name = repo.url.replace('https://github.com/', '')
        all_tasks = Task.query.filter_by(user_id=current_user.id, repository_id=task.repository_id).all()
        tasks_json = json.dumps([t.to_dict() for t in all_tasks], indent=2)
        
        sha = GithubService.push_commit(
            user=current_user,
            repo_name=repo_full_name,
            file_path=".devtrack/tasks.json",
            content=tasks_json,
            commit_message=f"Update task: {task.title} ({task.status})"
        )
        # Record commit in DB
        new_commit = Commit(
            user_id=current_user.id,
            repository_id=task.repository_id,
            sha=sha,
            message=f"Update task: {task.title} ({task.status})",
            files_changed=".devtrack/tasks.json"
        )
        db.session.add(new_commit)
        db.session.commit()
    except Exception as e:
        print(f"GitHub Error: {e}")
        return jsonify({
            'success': False,
            'message': 'Task updated locally, but GitHub sync failed.',
            'error': str(e)
        }), 500
        
    return jsonify(task.to_dict())

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    repo_id = task.repository_id
    db.session.delete(task)
    db.session.commit()
    
    # Sync to GitHub
    try:
        repo = Repository.query.get(repo_id)
        repo_full_name = repo.url.replace('https://github.com/', '')
        all_tasks = Task.query.filter_by(user_id=current_user.id, repository_id=repo_id).all()
        tasks_json = json.dumps([t.to_dict() for t in all_tasks], indent=2)
        
        sha = GithubService.push_commit(
            user=current_user,
            repo_name=repo_full_name,
            file_path=".devtrack/tasks.json",
            content=tasks_json,
            commit_message="Delete task and sync"
        )
        # Record commit in DB
        new_commit = Commit(
            user_id=current_user.id,
            repository_id=repo_id,
            sha=sha,
            message="Delete task and sync",
            files_changed=".devtrack/tasks.json"
        )
        db.session.add(new_commit)
        db.session.commit()
    except Exception as e:
        print(f"GitHub Error: {e}")
        return jsonify({
            'success': False,
            'message': 'Task deleted locally, but GitHub sync failed.',
            'error': str(e)
        }), 500
        
    return '', 204
