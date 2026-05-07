document.addEventListener('DOMContentLoaded', () => {
    const btnSaveProgress = document.getElementById('btn-save-progress');
    const commitPreviewBox = document.getElementById('commit-preview-box');

    if (btnSaveProgress) {
        btnSaveProgress.addEventListener('click', async () => {
            btnSaveProgress.disabled = true;
            btnSaveProgress.textContent = 'Committing...';
            
            try {
                const res = await fetch('/api/commit', { method: 'POST' });
                const data = await res.json();
                
                if (!res.ok) {
                    if (data.error && data.error.includes('Repository not linked')) {
                        // Prompt user to create repo
                        if (confirm('You need a GitHub repository to store your logs. Shall we create "devtrack-logs" on your GitHub account?')) {
                            await createRepo();
                        } else {
                            resetBtn();
                        }
                    } else {
                        alert(data.error || 'Failed to commit');
                        resetBtn();
                    }
                } else {
                    // Success is handled via socket event
                    // But we can reset here just in case
                }
            } catch (err) {
                alert('An error occurred');
                resetBtn();
            }
        });
    }

    async function createRepo() {
        btnSaveProgress.textContent = 'Creating Repo...';
        try {
            const res = await fetch('/repo/create', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_name: 'devtrack-logs' })
            });
            const data = await res.json();
            
            if (res.ok) {
                alert(`Repository ready: ${data.repo_url}. Now pushing commit...`);
                // Trigger commit again
                btnSaveProgress.textContent = 'Committing...';
                const commitRes = await fetch('/api/commit', { method: 'POST' });
                const commitData = await commitRes.json();
                
                if (!commitRes.ok) {
                    alert(commitData.error || 'Failed to commit after creating repo');
                    resetBtn();
                }
            } else {
                alert(data.error || 'Failed to create repo');
                resetBtn();
            }
        } catch (err) {
            alert('Error creating repo');
            resetBtn();
        }
    }

    function resetBtn() {
        btnSaveProgress.disabled = false;
        btnSaveProgress.textContent = 'Save Progress & Commit';
    }

    if (typeof socket !== 'undefined') {
        socket.on('commit:pushed', (data) => {
            resetBtn();
            commitPreviewBox.style.display = 'block';
            commitPreviewBox.innerHTML = `
                <div style="padding: 10px; background-color: var(--accent-green); color: white; border-radius: 4px; margin-top: 10px;">
                    ✅ <strong>Committed successfully!</strong><br>
                    SHA: <a href="https://github.com/${current_user_username}/devtrack-logs/commit/${data.sha}" target="_blank" style="color: white; text-decoration: underline;">${data.sha.substring(0, 7)}</a><br>
                    Message: ${data.message}
                </div>
            `;
            setTimeout(() => {
                commitPreviewBox.style.display = 'none';
            }, 10000); // Hide after 10 seconds
        });
    }
});
