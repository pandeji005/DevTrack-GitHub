document.addEventListener('DOMContentLoaded', () => {
    fetchStreaks();
    fetchHeatmap();
    
    // Listen for WebSocket events to update analytics
    if (typeof socket !== 'undefined') {
        socket.on('commit:pushed', (data) => {
            if (data.streak !== undefined) {
                document.getElementById('current-streak-val').textContent = data.streak;
            } else {
                fetchStreaks();
            }
            fetchHeatmap();
        });
    }
});

async function fetchStreaks() {
    try {
        const res = await fetch('/api/analytics/streaks');
        if (res.ok) {
            const data = await res.json();
            document.getElementById('current-streak-val').textContent = data.current_streak;
            document.getElementById('longest-streak-val').textContent = data.longest_streak;
            document.getElementById('total-commits-val').textContent = data.total_commits;
        }
    } catch (e) {
        console.error("Failed to fetch streaks", e);
    }
}

async function fetchHeatmap() {
    try {
        const res = await fetch('/api/analytics/heatmap');
        if (res.ok) {
            const data = await res.json();
            renderHeatmap(data);
        }
    } catch (e) {
        console.error("Failed to fetch heatmap", e);
    }
}

function renderHeatmap(data) {
    const grid = document.getElementById('heatmap-grid');
    grid.innerHTML = '';
    
    // Generate dates for the last 365 days
    const today = new Date();
    const startDate = new Date();
    startDate.setDate(today.getDate() - 364);
    
    // Adjust to start on a Sunday so the grid aligns correctly (optional, but good for GitHub style)
    const startDay = startDate.getDay();
    startDate.setDate(startDate.getDate() - startDay);
    
    const totalDays = Math.floor((today - startDate) / (1000 * 60 * 60 * 24)) + 1;
    
    for (let i = 0; i < totalDays; i++) {
        const d = new Date(startDate);
        d.setDate(startDate.getDate() + i);
        const dateStr = d.toISOString().split('T')[0];
        
        const count = data[dateStr] || 0;
        let level = 0;
        if (count > 0 && count <= 2) level = 1;
        else if (count > 2 && count <= 4) level = 2;
        else if (count > 4 && count <= 6) level = 3;
        else if (count > 6) level = 4;
        
        const cell = document.createElement('div');
        cell.className = 'heatmap-cell';
        cell.dataset.level = level;
        
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = `${count} commit${count !== 1 ? 's' : ''} on ${dateStr}`;
        cell.appendChild(tooltip);
        
        grid.appendChild(cell);
    }
}
