/**
 * DevTrack Documentation System
 */

class DocsManager {
    constructor() {
        this.docs = [];
        this.init();
    }

    init() {
        this.elements = {
            docsList: document.getElementById('docs-list'),
            viewer: document.getElementById('doc-viewer'),
            emptyState: document.getElementById('doc-empty-state')
        };

        document.querySelector('[data-view="docs"]').addEventListener('click', () => {
            if (this.docs.length === 0) this.loadDocs();
        });
    }

    async loadDocs() {
        try {
            // First try to look into 'docs' folder
            let res = await fetch('/api/repos/contents?path=docs');
            if (!res.ok) {
                // If no docs folder, try root
                res = await fetch('/api/repos/contents?path=');
            }
            
            if (res.ok) {
                const data = await res.json();
                this.docs = data.filter(item => item.name.endsWith('.md') || item.type === 'dir');
                this.renderDocsList();
            }
        } catch (err) {
            console.error('Failed to load documentation:', err);
        }
    }

    renderDocsList() {
        this.elements.docsList.innerHTML = '';
        
        if (this.docs.length === 0) {
            this.elements.docsList.innerHTML = '<p class="text-muted">No documentation found.</p>';
            return;
        }

        this.docs.forEach(doc => {
            const item = document.createElement('div');
            item.className = 'doc-item';
            item.innerHTML = `
                <i class="fas fa-book-open"></i>
                <span>${doc.name.replace('.md', '')}</span>
            `;
            item.onclick = () => this.openDoc(doc);
            this.elements.docsList.appendChild(item);
        });
    }

    async openDoc(doc) {
        // Remove active class from all
        document.querySelectorAll('.doc-item').forEach(i => i.classList.remove('active'));
        // Add to current target if needed (need a way to track which item was clicked)
        
        try {
            const res = await fetch(`/api/repos/contents?path=${doc.path}`);
            if (res.ok) {
                const data = await res.json();
                this.elements.viewer.innerHTML = marked.parse(data.content || '');
                this.elements.viewer.style.display = 'block';
                this.elements.emptyState.style.display = 'none';
                
                // Highlight code blocks in docs
                if (window.hljs) {
                    this.elements.viewer.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
                }
            }
        } catch (err) {
            console.error('Failed to open document:', err);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.docsManager = new DocsManager();
});
