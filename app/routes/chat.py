from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from app.models import Task, Log, Commit
from app.services.ai_service import AIService
from datetime import datetime, timedelta

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    query = data.get('message', '')
    
    if not query:
        return jsonify({'error': 'Message is required'}), 400
        
    # Initialize session history if not present
    if 'chat_history' not in session:
        session['chat_history'] = []
        
    # Gather last 7 days of context
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    recent_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.status == 'done',
        Task.completed_at >= week_ago
    ).all()
    
    recent_logs = Log.query.filter(
        Log.user_id == current_user.id,
        Log.date >= week_ago.date()
    ).all()
    
    context = "=== COMPLETED TASKS (Last 7 Days) ===\n"
    for t in recent_tasks:
        context += f"- [{t.completed_at.strftime('%Y-%m-%d')}] {t.title}\n"
        
    context += "\n=== LOGS (Last 7 Days) ===\n"
    for l in recent_logs:
        context += f"- [{l.date.isoformat()}] {l.content[:100]}...\n"
        
    try:
        # Get bot reply using history
        reply = AIService.chat_with_data(query, context, history=session['chat_history'])
        
        # Update history in session
        new_history = session['chat_history']
        new_history.append({"role": "user", "content": query})
        new_history.append({"role": "assistant", "content": reply})
        
        # Keep only last 10 messages to avoid context bloat
        session['chat_history'] = new_history[-10:]
        session.modified = True
        
        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
