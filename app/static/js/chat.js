document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chat-input');
    const btnSendChat = document.getElementById('btn-send-chat');
    const chatBody = document.getElementById('chat-body');
    const btnToggleChat = document.getElementById('btn-toggle-chat');
    const chatWidget = document.getElementById('ai-chat-widget');
    
    let isCollapsed = false;

    btnToggleChat.addEventListener('click', () => {
        isCollapsed = !isCollapsed;
        if (isCollapsed) {
            chatBody.style.display = 'none';
            document.querySelector('.chat-input-area').style.display = 'none';
            btnToggleChat.textContent = '+';
            chatWidget.style.height = 'auto';
        } else {
            chatBody.style.display = 'flex';
            document.querySelector('.chat-input-area').style.display = 'flex';
            btnToggleChat.textContent = '_';
            chatWidget.style.height = '400px';
        }
    });

    btnSendChat.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // Append user message
        appendMessage('user', text);
        chatInput.value = '';
        
        // Show typing indicator
        const typingId = 'typing-' + Date.now();
        appendMessage('ai', 'Thinking...', typingId);

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            
            // Remove typing indicator
            document.getElementById(typingId).remove();
            
            if (res.ok) {
                // Parse markdown if available
                const htmlContent = typeof marked !== 'undefined' ? marked.parse(data.reply) : data.reply;
                appendMessage('ai', htmlContent, null, true);
            } else {
                appendMessage('error', data.error || 'Failed to get a response.');
            }
        } catch (err) {
            document.getElementById(typingId).remove();
            appendMessage('error', 'Network error.');
        }
    }

    function appendMessage(role, content, id = null, isHtml = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${role}`;
        if (id) msgDiv.id = id;
        
        if (isHtml) {
            msgDiv.innerHTML = content;
        } else {
            msgDiv.textContent = content;
        }
        
        chatBody.appendChild(msgDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }
});
