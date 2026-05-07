from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from app.models.note import Note, Folder
from app.models.repository import Repository
from app import db

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/api/folders', methods=['GET'])
@login_required
def get_folders():
    repo_id = session.get('current_repo_id')
    if not repo_id:
        return jsonify({'error': 'No repository selected'}), 400
    
    folders = Folder.query.filter_by(repository_id=repo_id).all()
    return jsonify([{
        'id': f.id,
        'name': f.name,
        'notes_count': len(f.notes)
    } for f in folders])

@notes_bp.route('/api/folders', methods=['POST'])
@login_required
def create_folder():
    repo_id = session.get('current_repo_id')
    if not repo_id:
        return jsonify({'error': 'No repository selected'}), 400
    
    data = request.get_json()
    new_folder = Folder(
        repository_id=repo_id,
        name=data.get('name', 'New Folder')
    )
    db.session.add(new_folder)
    db.session.commit()
    return jsonify({'id': new_folder.id, 'name': new_folder.name})

@notes_bp.route('/api/notes', methods=['GET'])
@login_required
def get_notes():
    repo_id = session.get('current_repo_id')
    if not repo_id:
        return jsonify({'error': 'No repository selected'}), 400
    
    folder_id = request.args.get('folder_id')
    query = Note.query.filter_by(repository_id=repo_id)
    
    if folder_id:
        query = query.filter_by(folder_id=folder_id)
    
    notes = query.order_by(Note.updated_at.desc()).all()
    return jsonify([n.to_dict() for n in notes])

@notes_bp.route('/api/notes', methods=['POST'])
@login_required
def create_note():
    repo_id = session.get('current_repo_id')
    if not repo_id:
        return jsonify({'error': 'No repository selected'}), 400
    
    data = request.get_json()
    new_note = Note(
        repository_id=repo_id,
        folder_id=data.get('folder_id'),
        title=data.get('title', 'Untitled Note'),
        content=data.get('content', '')
    )
    db.session.add(new_note)
    db.session.commit()
    return jsonify(new_note.to_dict())

@notes_bp.route('/api/notes/<int:note_id>', methods=['GET'])
@login_required
def get_note(note_id):
    note = Note.query.get_or_404(note_id)
    return jsonify(note.to_dict())

@notes_bp.route('/api/notes/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    note = Note.query.get_or_404(note_id)
    data = request.get_json()
    
    note.title = data.get('title', note.title)
    note.content = data.get('content', note.content)
    note.folder_id = data.get('folder_id', note.folder_id)
    
    db.session.commit()
    return jsonify(note.to_dict())

@notes_bp.route('/api/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return '', 204

@notes_bp.route('/api/folders/<int:folder_id>', methods=['PATCH'])
@login_required
def rename_folder(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    data = request.get_json()
    folder.name = data.get('name', folder.name)
    db.session.commit()
    return jsonify({'id': folder.id, 'name': folder.name})

@notes_bp.route('/api/folders/<int:folder_id>', methods=['DELETE'])
@login_required
def delete_folder(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    db.session.delete(folder)
    db.session.commit()
    return '', 204
