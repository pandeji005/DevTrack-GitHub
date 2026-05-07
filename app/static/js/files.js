/**
 * DevTrack File Explorer (GitHub-style)
 */

class FileExplorer {
    constructor() {
        this.currentPath = '';
        this.init();
    }

    init() {
        this.elements = {
            tree: document.getElementById('files-tree'),
            contentContainer: document.getElementById('file-content-container'),
            emptyState: document.getElementById('file-empty-state'),
            pathDisplay: document.getElementById('active-file-path'),
            codeArea: document.getElementById('file-code')
        };

        // Listen for view changes to load initial tree
        document.querySelector('[data-view="files"]').addEventListener('click', () => {
            if (this.currentPath === '') this.loadContents('');
        });
    }

    async loadContents(path) {
        try {
            const res = await fetch(`/api/repos/contents?path=${path}`);
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data)) {
                    this.renderTree(data, path);
                } else {
                    this.renderFile(data);
                }
            }
        } catch (err) {
            console.error('Failed to load contents:', err);
        }
    }

    renderTree(items, path) {
        this.elements.tree.innerHTML = '';
        
        // Add "Back" button if not in root
        if (path !== '') {
            const parentPath = path.includes('/') ? path.split('/').slice(0, -1).join('/') : '';
            const backItem = document.createElement('div');
            backItem.className = 'tree-item directory';
            backItem.innerHTML = `<i class="fas fa-arrow-left"></i> <span>..</span>`;
            backItem.onclick = () => this.loadContents(parentPath);
            this.elements.tree.appendChild(backItem);
        }

        items.sort((a, b) => {
            if (a.type === b.type) return a.name.localeCompare(b.name);
            return a.type === 'dir' ? -1 : 1;
        }).forEach(item => {
            const el = document.createElement('div');
            el.className = `tree-item ${item.type}`;
            const icon = item.type === 'dir' ? 'fa-folder' : 'fa-file-code';
            el.innerHTML = `<i class="fas ${icon}"></i> <span>${item.name}</span>`;
            el.onclick = () => this.loadContents(item.path);
            this.elements.tree.appendChild(el);
        });
    }

    renderFile(file) {
        this.elements.contentContainer.classList.remove('hidden');
        this.elements.emptyState.classList.add('hidden');
        this.elements.pathDisplay.textContent = file.path;
        
        this.elements.codeArea.textContent = file.content;
        
        // Apply syntax highlighting
        if (window.hljs) {
            hljs.highlightElement(this.elements.codeArea);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.fileExplorer = new FileExplorer();
});
