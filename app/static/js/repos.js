/**
 * Unified UI Modal System
 */
const UI = {
    modal: document.getElementById('modal-container'),
    title: document.getElementById('modal-title'),
    body: document.getElementById('modal-body'),
    confirmBtn: document.getElementById('btn-modal-confirm'),
    cancelBtn: document.getElementById('btn-modal-cancel'),
    closeBtn: document.getElementById('btn-modal-close'),

    showModal(title, contentHtml, onConfirm, showFooter = true) {
        this.title.textContent = title;
        this.body.innerHTML = contentHtml;
        this.modal.classList.add('active');
        
        const footer = document.getElementById('modal-footer');
        footer.style.display = showFooter ? 'flex' : 'none';

        const close = () => {
            this.modal.classList.remove('active');
            this.confirmBtn.onclick = null;
            this.cancelBtn.onclick = null;
        };

        this.closeBtn.onclick = close;
        this.cancelBtn.onclick = close;
        this.confirmBtn.onclick = () => {
            if (onConfirm()) close();
        };
    },

    prompt(title, message) {
        return new Promise((resolve) => {
            const content = `
                <p style="margin-bottom: 1rem; color: var(--text-secondary);">${message}</p>
                <input type="text" id="modal-prompt-input" class="search-container" style="width: 100%; background: var(--bg-primary);" autofocus>
            `;
            
            this.showModal(title, content, () => {
                const val = document.getElementById('modal-prompt-input').value;
                resolve(val);
                return true;
            });
            
            this.cancelBtn.onclick = () => {
                this.modal.classList.remove('active');
                resolve(null);
            };
        });
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const repoSelect = document.querySelector('.repo-select');
    const activeRepoName = document.getElementById('active-repo-name');
    
    // Fetch and populate repositories
    async function loadRepositories() {
        try {
            const response = await fetch('/api/repos');
            const repos = await response.json();
            
            repoSelect.innerHTML = '<option value="">Select Workspace...</option>';
            
            if (repos.length > 0) {
                repos.forEach(repo => {
                    const option = document.createElement('option');
                    option.value = repo.id;
                    option.textContent = repo.name;
                    repoSelect.appendChild(option);
                });
            }
            
            const divider = document.createElement('option');
            divider.disabled = true;
            divider.textContent = "──────────";
            repoSelect.appendChild(divider);

            const createOption = document.createElement('option');
            createOption.value = "CREATE_NEW";
            createOption.textContent = "+ New Local Workspace";
            repoSelect.appendChild(createOption);

            const importOption = document.createElement('option');
            importOption.value = "IMPORT_GITHUB";
            importOption.textContent = "☁ Import from GitHub";
            repoSelect.appendChild(importOption);
            
            const currentResponse = await fetch('/api/repos/current');
            const currentRepo = await currentResponse.json();
            if (currentRepo) {
                repoSelect.value = currentRepo.id;
                if (activeRepoName) activeRepoName.textContent = currentRepo.name;
            } else {
                if (activeRepoName) activeRepoName.textContent = "No Workspace Selected";
            }
        } catch (error) {
            console.error('Error loading repositories:', error);
        }
    }

    repoSelect.addEventListener('change', async (e) => {
        const val = e.target.value;
        
        if (val === "CREATE_NEW") {
            const name = await UI.prompt("Create Workspace", "Enter a name for your new local workspace:");
            if (name) {
                const response = await fetch('/api/repos', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });
                if (response.ok) {
                    window.location.reload();
                }
            } else {
                repoSelect.value = "";
            }
            return;
        }

        if (val === "IMPORT_GITHUB") {
            handleGithubImport();
            return;
        }

        if (val) {
            const response = await fetch('/api/repos/select', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_id: val })
            });
            if (response.ok) {
                window.location.reload();
            }
        }
    });

    async function handleGithubImport() {
        repoSelect.innerHTML = '<option>Loading GitHub repos...</option>';
        try {
            const res = await fetch('/api/repos/github/list');
            const githubRepos = await res.json();
            
            if (githubRepos.error) {
                UI.showModal("Connection Error", `<p>${githubRepos.error}</p>`, () => true);
                loadRepositories();
                return;
            }

            let listHtml = '<div class="repo-list-modal">';
            githubRepos.slice(0, 20).forEach((r, i) => {
                listHtml += `
                    <div class="repo-import-item" data-index="${i}">
                        <span>${r.name}</span>
                        <i class="fas fa-download"></i>
                    </div>
                `;
            });
            listHtml += '</div>';
            
            UI.showModal("Import Repository", listHtml, () => false, false);
            
            // Handle clicks inside the custom modal
            document.querySelectorAll('.repo-import-item').forEach(item => {
                item.onclick = async () => {
                    const index = item.getAttribute('data-index');
                    const repo = githubRepos[index];
                    
                    UI.body.innerHTML = `<p>Importing <strong>${repo.name}</strong>...</p>`;
                    
                    const importRes = await fetch('/api/repos/github/import', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            name: repo.name,
                            url: repo.url
                        })
                    });
                    
                    if (importRes.ok) {
                        window.location.reload();
                    } else {
                        UI.modal.classList.add('hidden');
                        loadRepositories();
                    }
                };
            });

        } catch (err) {
            UI.showModal("Error", "<p>Failed to fetch GitHub repositories.</p>", () => true);
            loadRepositories();
        }
    }

    loadRepositories();
});

