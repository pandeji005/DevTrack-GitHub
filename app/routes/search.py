from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from app.models.task import Task
from app.models.log import Log
from app.models import db

search_bp = Blueprint('search', __name__, url_prefix='/api/search')

@search_bp.route('/global')
@login_required
def global_search():
    query = request.args.get('q', '')
    repo_id = session.get('current_repo_id')
    
    if not query or not repo_id:
        return jsonify([])

    results = []

    # Search Tasks
    tasks = Task.query.filter_by(repository_id=repo_id).filter(
        (Task.title.ilike(f'%{query}%')) | (Task.description.ilike(f'%{query}%'))
    ).limit(5).all()

    for task in tasks:
        results.append({
            'type': 'task',
            'id': task.id,
            'title': task.title,
            'subtitle': f'Task • {task.status.replace("_", " ").capitalize()}',
            'url': f'/tasks'
        })

    # Search Logs
    logs = Log.query.filter_by(repository_id=repo_id).filter(
        Log.content.ilike(f'%{query}%')
    ).limit(5).all()

    for log in logs:
        results.append({
            'type': 'log',
            'id': log.id,
            'title': f"Log - {log.date.strftime('%b %d, %Y')}",
            'subtitle': (log.content[:60] + '...') if log.content else 'No content',
            'url': f'/logs'
        })

    return jsonify(results)
