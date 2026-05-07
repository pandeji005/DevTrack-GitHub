/**
 * DevTrack Notes System (Notion-style)
 */

class NotesManager {
    constructor() {
        this.currentNote = null;
        this.notes = [];
        this.folders = [];
        this.init();
    }

    async init() {
        this.elements = {
            notesList: document.getElementById('notes-list'),
            editorContainer: document.getElementById('note-editor-container'),
            emptyState: document.getElementById('note-empty-state'),
            titleInput: document.getElementById('note-title-input'),
            contentInput: document.getElementById('note-content-input'),
            previewArea: document.getElementById('note-preview'),
            btnNewNote: document.getElementById('btn-new-note')
        };

        if (this.elements.btnNewNote) {
            this.elements.btnNewNote.addEventListener('click', () => this.createNewNote());
        }

        this.elements.titleInput.addEventListener('input', () => this.handleTitleInput());
        this.elements.contentInput.addEventListener('input', () => this.handleContentInput());

        await this.loadFolders();
        await this.loadNotes();
    }

    async loadFolders() {
        try {
            const res = await fetch('/api/folders');
            if (res.ok) {
                this.folders = await res.json();
            }
        } catch (err) {
            console.error('Failed to load folders:', err);
        }
    }

    async loadNotes(folderId = null) {
        try {
            let url = '/api/notes';
            if (folderId) url += `?folder_id=${folderId}`;
            
            const res = await fetch(url);
            if (res.ok) {
                this.notes = await res.json();
                this.renderNotesList();
            }
        } catch (err) {
            console.error('Failed to load notes:', err);
        }
    }

    renderNotesList() {
        this.elements.notesList.innerHTML = '';
        
        if (this.notes.length === 0) {
            this.elements.notesList.innerHTML = '<p class="text-muted p-3">No notes yet.</p>';
            return;
        }

        this.notes.forEach(note => {
            const item = document.createElement('div');
            item.className = `note-item ${this.currentNote && this.currentNote.id === note.id ? 'active' : ''}`;
            item.innerHTML = `
                <i class="far fa-file-alt"></i>
                <span class="note-title-text">${note.title || 'Untitled'}</span>
            `;
            item.addEventListener('click', () => this.openNote(note));
            this.elements.notesList.appendChild(item);
        });
    }

    async createNewNote(folderId = null) {
        try {
            const res = await fetch('/api/notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: 'Untitled Note',
                    content: '',
                    folder_id: folderId
                })
            });
            
            if (res.ok) {
                const newNote = await res.json();
                this.notes.unshift(newNote);
                this.renderNotesList();
                this.openNote(newNote);
            }
        } catch (err) {
            console.error('Failed to create note:', err);
        }
    }

    openNote(note) {
        this.currentNote = note;
        this.elements.editorContainer.classList.remove('hidden');
        this.elements.emptyState.classList.add('hidden');
        
        this.elements.titleInput.value = note.title;
        this.elements.contentInput.value = note.content;
        
        this.updatePreview();
        this.renderNotesList();
    }

    handleTitleInput() {
        if (!this.currentNote) return;
        this.currentNote.title = this.elements.titleInput.value;
        
        // Update list UI instantly
        const activeItem = this.elements.notesList.querySelector('.note-item.active .note-title-text');
        if (activeItem) activeItem.textContent = this.currentNote.title || 'Untitled';
        
        this.debounceSave();
    }

    handleContentInput() {
        if (!this.currentNote) return;
        this.currentNote.content = this.elements.contentInput.value;
        this.updatePreview();
        this.debounceSave();
    }

    updatePreview() {
        if (window.marked) {
            this.elements.previewArea.innerHTML = marked.parse(this.elements.contentInput.value);
        }
    }

    debounceSave() {
        if (this.saveTimeout) clearTimeout(this.saveTimeout);
        this.saveTimeout = setTimeout(() => this.saveCurrentNote(), 1000);
    }

    async saveCurrentNote() {
        if (!this.currentNote) return;
        
        try {
            const res = await fetch(`/api/notes/${this.currentNote.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: this.currentNote.title,
                    content: this.currentNote.content
                })
            });
            
            if (res.ok) {
                console.log('Note auto-saved');
            }
        } catch (err) {
            console.error('Failed to auto-save note:', err);
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.notesManager = new NotesManager();
});
