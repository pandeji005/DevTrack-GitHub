from flask import Flask, render_template, jsonify, redirect, url_for, session
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_migrate import Migrate
from .config import Config
from .models import db, User

login_manager = LoginManager()
socketio = SocketIO()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'index'
    
    # Standard CORS for single-origin Flask app
    CORS(app)
    
    # Initialize SocketIO
    async_mode = app.config.get('SOCKET_ASYNC_MODE', 'eventlet')
    socketio.init_app(app, async_mode=async_mode, cors_allowed_origins="*")
    
    from app.sockets import events

    from app.routes.auth import auth_bp
    from app.routes.repo import repo_bp
    from app.routes.analytics import analytics_bp
    from app.routes.notes import notes_bp
    from app.routes.logs import logs_bp
    from app.routes.tasks import tasks_bp
    from app.routes.chat import chat_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(repo_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(chat_bp)

    @app.context_processor
    def inject_repo():
        repo_id = session.get('current_repo_id')
        if repo_id:
            from app.models import Repository
            repo = Repository.query.get(repo_id)
            return dict(current_repo=repo)
        return dict(current_repo=None)

    # Basic routes — Flask still serves landing + legacy dashboard
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('landing.html')

    @app.route('/dashboard')
    def dashboard():
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        
        # Check if a repo is selected in session
        if not session.get('current_repo_id'):
            # Try to pick the most recent one
            from app.models import Repository
            repo = Repository.query.filter_by(user_id=current_user.id).order_by(Repository.created_at.desc()).first()
            if repo:
                session['current_repo_id'] = repo.id
            else:
                # If no repos exist, redirect to setup
                return redirect(url_for('setup'))

        from app.models import Task
        active_tasks_count = Task.query.filter_by(repository_id=session.get('current_repo_id')).filter(Task.status != 'done').count()

        return render_template('dashboard.html', active_page='dashboard', active_tasks_count=active_tasks_count)

    @app.route('/setup')
    def setup():
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        return render_template('setup.html', active_page='setup')

    @app.route('/tasks')
    def tasks_page():
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        return render_template('tasks_page.html', active_page='tasks')

    @app.route('/logs')
    def logs_page():
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        return render_template('logs_page.html', active_page='logs')

    @app.route('/activity')
    def activity():
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        return render_template('activity.html', active_page='activity')

    @app.route('/settings')
    def settings():
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        return render_template('settings.html', active_page='settings')

    @app.route('/docs')
    def docs():
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        return render_template('docs.html', active_page='docs')

    @app.route('/documents')
    def documents_page():
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        return render_template('documents.html', active_page='documents')

    # Create DB tables
    with app.app_context():
        db.create_all()
    
    return app
