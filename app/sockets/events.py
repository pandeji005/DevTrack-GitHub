from flask_socketio import join_room
from flask_login import current_user
from app import socketio

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        room = f"user_{current_user.id}"
        join_room(room)
        # print(f"User {current_user.username} joined room {room}")
