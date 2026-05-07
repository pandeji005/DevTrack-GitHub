document.addEventListener('DOMContentLoaded', () => {
    const tasksTodo = document.getElementById('tasks-todo');
    const tasksInProgress = document.getElementById('tasks-inprogress');
    const tasksDone = document.getElementById('tasks-done');
    const taskForm = document.getElementById('task-form');

    // Fetch and render initial tasks
    async function loadTasks() {
        const res = await fetch('/api/tasks');
        const tasks = await res.json();
        
        // Clear containers
        if (tasksTodo) tasksTodo.innerHTML = '';
        if (tasksInProgress) tasksInProgress.innerHTML = '';
        if (tasksDone) tasksDone.innerHTML = '';
        
        tasks.forEach(task => renderTask(task));
    }

    // Create a new task
    if (taskForm) {
        taskForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const titleInput = document.getElementById('task-title');
            const typeSelect = document.getElementById('task-type');
            const prioritySelect = document.getElementById('task-priority');

            fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: titleInput.value,
                    type: typeSelect.value,
                    priority: prioritySelect.value
                })
            }).then(() => {
                titleInput.value = '';
                // Close modal if exists
                const taskModal = document.getElementById('task-modal-overlay');
                const taskContent = document.getElementById('task-modal-content');
                if (taskModal) {
                    taskContent.classList.remove('scale-100', 'opacity-100');
                    taskContent.classList.add('scale-90', 'opacity-0');
                    setTimeout(() => taskModal.classList.add('hidden'), 300);
                }
            });
        });
    }

    // Handle WebSocket events
    if (typeof socket !== 'undefined') {
        socket.on('task:created', (task) => {
            renderTask(task);
        });

        socket.on('task:updated', (task) => {
            const oldTaskEl = document.getElementById(`task-${task.id}`);
            if (oldTaskEl) oldTaskEl.remove();
            renderTask(task);
        });

        socket.on('task:deleted', (data) => {
            const taskEl = document.getElementById(`task-${data.task_id}`);
            if (taskEl) taskEl.remove();
        });
    }

    function renderTask(task) {
        const column = getColumnByStatus(task.status);
        if (!column) return;
        
        const taskEl = document.createElement('div');
        taskEl.className = 'task-row';
        taskEl.id = `task-${task.id}`;
        taskEl.innerHTML = createTaskHTML(task);
        
        column.appendChild(taskEl);
        attachTaskListeners(task.id, task.status);
    }

    function getColumnByStatus(status) {
        if (status === 'pending') return tasksTodo;
        if (status === 'in_progress') return tasksInProgress;
        if (status === 'done') return tasksDone;
        return null;
    }

    function createTaskHTML(task) {
        const isDone = task.status === 'done';
        
        const priorityClasses = {
            'low': 'priority-low',
            'medium': 'priority-medium',
            'high': 'priority-high',
            'critical': 'priority-high'
        };

        const statusIcons = {
            'pending': '<span class="material-symbols-outlined status-todo">radio_button_unchecked</span>',
            'in_progress': '<span class="material-symbols-outlined status-inprogress animate-pulse">sync</span>',
            'done': '<span class="material-symbols-outlined status-done">check_circle</span>'
        };

        const priorityClass = priorityClasses[task.priority] || 'priority-medium';
        const statusIcon = statusIcons[task.status] || statusIcons['pending'];

        let actions = '';
        if (task.status === 'pending') {
            actions = `<button class="btn-start btn-ghost" title="Start Task"><span class="material-symbols-outlined">play_arrow</span></button>`;
        } else if (task.status === 'in_progress') {
            actions = `<button class="btn-complete btn-ghost" title="Complete Task" style="color: var(--accent-green);"><span class="material-symbols-outlined">check</span></button>`;
        }

        return `
            <div class="flex items-center justify-center">
                <input type="checkbox" ${isDone ? 'checked' : ''}>
            </div>
            <div class="task-title ${isDone ? 'text-muted line-through' : ''}">
                ${task.title}
            </div>
            <div class="task-meta ${priorityClass}">
                ${task.priority}
            </div>
            <div class="task-meta flex items-center gap-2">
                ${statusIcon}
                ${task.status.replace('_', ' ')}
            </div>
            <div>
                <span class="badge badge-blue">${task.type}</span>
            </div>
            <div class="flex items-center justify-end gap-1">
                ${actions}
                <button class="btn-delete btn-ghost" title="Delete" style="color: var(--accent-red);">
                    <span class="material-symbols-outlined">delete</span>
                </button>
            </div>
        `;
    }

    function attachTaskListeners(taskId, status) {
        const taskEl = document.getElementById(`task-${taskId}`);
        if (!taskEl) return;

        const startBtn = taskEl.querySelector('.btn-start');
        const completeBtn = taskEl.querySelector('.btn-complete');
        const deleteBtn = taskEl.querySelector('.btn-delete');

        if (startBtn) {
            startBtn.addEventListener('click', () => {
                updateTaskStatus(taskId, 'in_progress');
            });
        }

        if (completeBtn) {
            completeBtn.addEventListener('click', () => {
                updateTaskStatus(taskId, 'done');
            });
        }

        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                if (confirm('Delete this task?')) {
                    fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
                }
            });
        }
    }

    async function updateTaskStatus(taskId, status) {
        await fetch(`/api/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: status })
        });
    }

    loadTasks();
});
