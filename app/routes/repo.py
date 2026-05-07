from datetime import datetime
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from app.models import db, Repository
from app.services.github_service import GithubService

repo_bp = Blueprint('repo', __name__, url_prefix='/api/repos')

@repo_bp.route('', methods=['GET'])
@login_required
def get_repos():
    try:
        repos = Repository.query.filter_by(user_id=current_user.id).order_by(Repository.created_at.desc()).all()
        return jsonify([repo.to_dict() for repo in repos])
    except Exception as e:
        print(f"DEBUG: Error in get_repos: {str(e)}")
        return jsonify({'error': str(e)}), 500

@repo_bp.route('', methods=['POST'])
@login_required
def create_repo():
    data = request.get_json()
    name = data.get('name')
    url = data.get('url', '')
    visibility = data.get('visibility', 'public')
    
    if not name:
        return jsonify({'error': 'Repository name is required'}), 400
        
    repo = Repository(
        user_id=current_user.id,
        name=name,
        url=url,
        visibility=visibility
    )
    
    db.session.add(repo)
    db.session.commit()
    
    # Auto-select the newly created repo
    session['current_repo_id'] = repo.id
    
    return jsonify(repo.to_dict()), 201

@repo_bp.route('/select', methods=['POST'])
@login_required
def select_repo():
    data = request.get_json()
    repo_id = data.get('repo_id')
    
    if not repo_id:
        return jsonify({'error': 'repo_id is required'}), 400
        
    repo = Repository.query.filter_by(id=repo_id, user_id=current_user.id).first()
    if not repo:
        return jsonify({'error': 'Repository not found'}), 404
        
    session['current_repo_id'] = repo.id
    return jsonify({'success': True, 'current_repo_id': repo.id})

@repo_bp.route('/current', methods=['GET'])
@login_required
def get_current_repo():
    repo_id = session.get('current_repo_id')
    if not repo_id:
        # If no repo is selected, pick the most recent one
        repo = Repository.query.filter_by(user_id=current_user.id).order_by(Repository.created_at.desc()).first()
        if repo:
            session['current_repo_id'] = repo.id
            return jsonify(repo.to_dict())
        return jsonify(None)
        
    repo = Repository.query.filter_by(id=repo_id, user_id=current_user.id).first()
    if not repo:
        session.pop('current_repo_id', None)
        return jsonify(None)
        
    return jsonify(repo.to_dict())

@repo_bp.route('/github/list', methods=['GET'])
@login_required
def list_github_repos():
    print("DEBUG: Starting list_github_repos")
    try:
        print(f"DEBUG: Fetching repos for user {current_user.username}")
        # Aggressive limit: only fetch first page (30 repos) for speed
        repos = GithubService.list_repos(current_user).get_page(0)
        repo_list = []
        for r in repos:
            repo_list.append({'name': r.name, 'full_name': r.full_name, 'url': r.html_url})
        print(f"DEBUG: Found {len(repo_list)} repos")
        return jsonify(repo_list)
    except Exception as e:
        print(f"DEBUG: Error in list_github_repos: {str(e)}")
        return jsonify({'error': str(e)}), 500

@repo_bp.route('/github/import', methods=['POST'])
@login_required
def import_github_repo():
    data = request.get_json()
    repo_name = data.get('name')
    repo_url = data.get('url')
    
    if not repo_name:
        return jsonify({'error': 'Repository name is required'}), 400
        
    # Check if already imported
    existing = Repository.query.filter_by(user_id=current_user.id, name=repo_name).first()
    if existing:
        session['current_repo_id'] = existing.id
        return jsonify(existing.to_dict())
        
    repo = Repository(
        user_id=current_user.id,
        name=repo_name,
        url=repo_url,
        visibility='public' # Default
    )
    
    db.session.add(repo)
    db.session.commit()
    
    session['current_repo_id'] = repo.id
    return jsonify(repo.to_dict()), 201

@repo_bp.route('/github/create', methods=['POST'])
@login_required
def create_github_repo():
    data = request.get_json()
    repo_name = data.get('name')
    private = data.get('private', False)
    
    if not repo_name:
        return jsonify({'error': 'Repository name is required'}), 400
        
    try:
        # Create on GitHub
        repo_gh, created = GithubService.create_repo(current_user, repo_name)
        
        # Save locally
        existing = Repository.query.filter_by(user_id=current_user.id, name=repo_name).first()
        if not existing:
            repo = Repository(
                user_id=current_user.id,
                name=repo_name,
                url=repo_gh.html_url,
                visibility='private' if private else 'public'
            )
            db.session.add(repo)
            db.session.commit()
            session['current_repo_id'] = repo.id
        else:
            session['current_repo_id'] = existing.id
            
        return jsonify({'success': True, 'repo': repo_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@repo_bp.route('/<int:repo_id>', methods=['PATCH'])
@login_required
def update_repo(repo_id):
    repo = Repository.query.filter_by(id=repo_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    if 'name' in data:
        repo.name = data['name']
    if 'description' in data:
        repo.description = data['description']
    if 'visibility' in data:
        repo.visibility = data['visibility']
    if 'language' in data:
        repo.language = data['language']
    db.session.commit()
    return jsonify(repo.to_dict())

@repo_bp.route('/<int:repo_id>', methods=['DELETE'])
@login_required
def delete_repo(repo_id):
    repo = Repository.query.filter_by(id=repo_id, user_id=current_user.id).first_or_404()
    if session.get('current_repo_id') == repo_id:
        session.pop('current_repo_id', None)
    db.session.delete(repo)
    db.session.commit()
    return '', 204
@repo_bp.route('/contents', methods=['GET'])
@login_required
def get_contents():
    repo_id = session.get('current_repo_id')
    if not repo_id:
        return jsonify({'error': 'No repository selected'}), 400
    
    repo = Repository.query.get(repo_id)
    if not repo:
        return jsonify({'error': 'Repository not found'}), 404
        
    path = request.args.get('path', '')
    
    # Get repo full name from URL
    # Assuming URL is like https://github.com/username/reponame
    if not repo.url:
        return jsonify({'error': 'Repository has no URL'}), 400
        
    repo_full_name = repo.url.replace('https://github.com/', '')
    
    try:
        contents = GithubService.get_repo_contents(current_user, repo_full_name, path)
        
        results = []
        if isinstance(contents, list):
            for item in contents:
                results.append({
                    'name': item.name,
                    'path': item.path,
                    'type': item.type, # 'dir' or 'file'
                    'size': item.size,
                    'download_url': item.download_url
                })
        else:
            # Single file
            results = {
                'name': contents.name,
                'path': contents.path,
                'type': contents.type,
                'content': contents.decoded_content.decode('utf-8') if contents.type == 'file' else None,
                'download_url': contents.download_url
            }
            
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@repo_bp.route('/file', methods=['POST'])
@login_required
def save_file():
    repo_id = session.get('current_repo_id')
    if not repo_id:
        return jsonify({'error': 'No repository selected'}), 400
    
    repo_db = Repository.query.get(repo_id)
    if not repo_db:
        return jsonify({'error': 'Repository not found'}), 404
        
    data = request.get_json()
    path = data.get('path')
    content = data.get('content', '')
    message = data.get('message', f'Update {path}')
    sha = data.get('sha') # Required for updates
    
    if not path:
        return jsonify({'error': 'Path is required'}), 400
        
    repo_full_name = repo_db.url.replace('https://github.com/', '').strip('/').replace('.git', '')
    
    try:
        # Use our centralized push_commit for better attribution and performance
        new_sha = GithubService.push_commit(
            current_user, 
            repo_full_name, 
            path, 
            content, 
            message
        )
            
        # Record local Commit for activity tracking
        from app.models import Commit
        new_commit = Commit(
            user_id=current_user.id,
            repository_id=repo_id,
            sha=new_sha,
            message=message,
            committed_at=datetime.utcnow()
        )
        db.session.add(new_commit)
        db.session.commit()

        return jsonify({
            'success': True,
            'commit': new_sha
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@repo_bp.route('/move', methods=['POST'])
@login_required
def move_file():
    repo_id = session.get('current_repo_id')
    if not repo_id:
        return jsonify({'error': 'No repository selected'}), 400
    
    repo_db = Repository.query.get(repo_id)
    data = request.get_json()
    old_path = data.get('old_path')
    new_path = data.get('new_path')
    
    if not old_path or not new_path:
        return jsonify({'error': 'Old and new paths are required'}), 400
        
    repo_full_name = repo_db.url.replace('https://github.com/', '').strip('/').replace('.git', '')
    
    try:
        g = GithubService.get_client(current_user)
        repo_gh = g.get_repo(repo_full_name)
        
        # Get old file content and SHA
        contents = repo_gh.get_contents(old_path)
        
        # Create at new path
        repo_gh.create_file(new_path, f"Move {old_path} to {new_path}", contents.decoded_content)
        
        # Delete at old path
        repo_gh.delete_file(old_path, f"Move {old_path} to {new_path}", contents.sha)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
