document.addEventListener('DOMContentLoaded', () => {
    const logEditor = document.getElementById('log-editor');
    const logPreview = document.getElementById('log-preview');
    const logStatus = document.getElementById('log-status');
    let saveTimeout;

    // Fetch today's log
    fetch('/api/logs/today')
        .then(res => res.json())
        .then(data => {
            if (data.content) {
                logEditor.value = data.content;
                renderMarkdown(data.content);
            }
        });

    logEditor.addEventListener('input', () => {
        const content = logEditor.value;
        renderMarkdown(content);
        
        logStatus.textContent = 'Saving...';
        
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => {
            saveLog(content);
        }, 1000); // Autosave after 1s of inactivity
    });

    function renderMarkdown(content) {
        if (typeof marked !== 'undefined') {
            logPreview.innerHTML = marked.parse(content || '*No content yet*');
        } else {
            logPreview.textContent = content;
        }
    }

    function saveLog(content) {
        fetch('/api/logs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        })
        .then(res => res.json())
        .then(data => {
            logStatus.textContent = 'Saved';
        })
        .catch(() => {
            logStatus.textContent = 'Error saving';
        });
    }

    if (typeof socket !== 'undefined') {
        socket.on('log:saved', (data) => {
            // Other tabs might need to update
            // For now, if we receive a socket event and we didn't just type it, we could sync it
            // Simple approach: ignore in current tab to prevent jumping cursor
        });
    }
});
