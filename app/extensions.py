from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import redis
from rq import Queue
from app.logging_config import log_rate_limit_event

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
migrate = Migrate()
csrf = CSRFProtect()

# Redis connection for RQ
redis_client = None
task_queue = None

def init_extensions(app):
    """Initialize all Flask extensions."""
    # SQLAlchemy
    db.init_app(app)
    
    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Flask-Limiter with custom handler
    limiter.init_app(app)
    
    # Custom rate limit handler
    @limiter.request_filter
    def ip_whitelist():
        # Add any IP whitelist logic here if needed
        return False
    
    @limiter.request_filter
    def log_rate_limits():
        # This will be called for every request
        return False
    
    # Flask-Migrate
    migrate.init_app(app, db)
    
    # Flask-WTF CSRF
    csrf.init_app(app)
    
    # Redis and RQ
    global redis_client, task_queue
    redis_client = redis.from_url(app.config.get('REDIS_URL', 'redis://localhost:6379'))
    task_queue = Queue(connection=redis_client)
    
    # User loader for Flask-Login
    from app.models.user import load_user
    login_manager.user_loader(load_user)
    
    return app
