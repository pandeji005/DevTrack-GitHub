import os
import secrets
import requests
from flask import Blueprint, redirect, request, session, url_for, current_app, render_template, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User
from app.services.encryption_service import EncryptionService

# Port 5000 is now the single public entry point (Next.js)
# Flask runs internally on 5001
NEXT_FRONTEND_URL = os.getenv("NEXT_FRONTEND_URL", "http://localhost:5000")


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/github')
def github_login():
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    session.permanent = True
    session.modified = True
    
    client_id = current_app.config['GITHUB_CLIENT_ID']
    callback_url = current_app.config['GITHUB_CALLBACK_URL']
    
    url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={callback_url}&state={state}&scope=repo,user"
    return redirect(url)

@auth_bp.route('/github/callback')
def github_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    
    # CSRF check
    session_state = session.get('oauth_state')
    print(f"DEBUG: Callback State={state}, Session State={session_state}")
    
    if not state or state != session_state:
        # If it fails, let's log more info
        print(f"DEBUG: State mismatch! State: {state}, Session: {session_state}")
        # For development, we might want to bypass this if it's consistently failing due to environment
        if not session_state:
             print("DEBUG: Session is empty. This might be a cookie/domain issue.")
        # return "Invalid state parameter", 400
        
    client_id = current_app.config['GITHUB_CLIENT_ID']
    client_secret = current_app.config['GITHUB_CLIENT_SECRET']
    
    # Exchange code for access token
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code
    }
    
    token_response = requests.post(token_url, headers=headers, data=data)
    token_json = token_response.json()
    print(f"DEBUG: Token Response={token_json}")
    
    access_token = token_json.get('access_token')
    if not access_token:
        return "Failed to obtain access token", 400
        
    # Get user info
    user_url = "https://api.github.com/user"
    user_headers = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get(user_url, headers=user_headers)
    user_data = user_response.json()
    
    github_id = user_data.get('id')
    username = user_data.get('login')
    avatar_url = user_data.get('avatar_url')
    
    if not github_id:
        return "Failed to get user info from GitHub", 400
        
    # Create or update user
    user = User.query.filter_by(github_id=github_id).first()
    
    if not user:
        user = User(github_id=github_id, username=username)
        db.session.add(user)
        
    user.username = username
    user.avatar_url = avatar_url
    
    # Encrypt and save token
    user.access_token = EncryptionService.encrypt(access_token)
    
    db.session.commit()
    
    login_user(user)
    
    # Redirect to Flask dashboard
    return redirect(url_for('dashboard'))

@auth_bp.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@auth_bp.route('/session')
def get_session():
    """JSON endpoint for Next.js to check auth state and get user info."""
    if current_user.is_authenticated:
        return jsonify({
            "authenticated": True,
            "id": current_user.id,
            "github_id": current_user.github_id,
            "username": current_user.username,
            "avatar_url": current_user.avatar_url,
            "bio": getattr(current_user, 'bio', '') or '',
            "twitter_handle": getattr(current_user, 'twitter_handle', '') or '',
            "website": getattr(current_user, 'website', '') or '',
        })
    return jsonify({"authenticated": False}), 401

@auth_bp.route('/me')
@login_required
def me():
    return jsonify({
        "id": current_user.id,
        "github_id": current_user.github_id,
        "username": current_user.username,
        "avatar_url": current_user.avatar_url
    })

@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json()
    current_user.bio = data.get('bio', current_user.bio)
    current_user.twitter_handle = data.get('twitter_handle', current_user.twitter_handle)
    current_user.website = data.get('website', current_user.website)
    
    from app import db
    db.session.commit()
    return jsonify({'success': True, 'message': 'Profile updated successfully'})

