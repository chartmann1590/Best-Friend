"""
Logging configuration for Best Friend AI Companion.
Provides structured logging with different levels and handlers.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from flask import request, has_request_context

class RequestFormatter(logging.Formatter):
    """Custom formatter that includes request context when available."""
    
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.method = request.method
            record.user_agent = request.headers.get('User-Agent', 'Unknown')
            if hasattr(request, 'user_id'):
                record.user_id = request.user_id
            else:
                record.user_id = 'anonymous'
        else:
            record.url = None
            record.remote_addr = None
            record.method = None
            record.user_agent = None
            record.user_id = None
        
        return super().format(record)

def setup_logging(app):
    """Setup comprehensive logging for the application."""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Remove default Flask logger
    app.logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = RequestFormatter(
        '%(asctime)s [%(levelname)s] %(name)s - '
        '%(message)s - '
        'URL: %(url)s | IP: %(remote_addr)s | '
        'Method: %(method)s | User: %(user_id)s | '
        'User-Agent: %(user_agent)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    )
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # File handler for all logs (DEBUG and above)
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Error file handler (ERROR and above)
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/errors.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Security log handler (WARNING and above)
    security_handler = logging.handlers.RotatingFileHandler(
        'logs/security.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(detailed_formatter)
    
    # Access log handler (INFO and above)
    access_handler = logging.handlers.RotatingFileHandler(
        'logs/access.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(detailed_formatter)
    
    # Set root logger level
    logging.getLogger().setLevel(logging.DEBUG)
    
    # Add handlers to root logger
    logging.getLogger().addHandler(console_handler)
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().addHandler(error_handler)
    logging.getLogger().addHandler(security_handler)
    logging.getLogger().addHandler(access_handler)
    
    # Set Flask app logger
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    
    # Set specific logger levels
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('gunicorn').setLevel(logging.INFO)
    
    # Log application startup
    app.logger.info("Logging system initialized")
    app.logger.info(f"Application environment: {app.config.get('FLASK_ENV', 'unknown')}")
    app.logger.info(f"Debug mode: {app.debug}")

def log_request_start():
    """Log the start of each request."""
    if has_request_context():
        logger = logging.getLogger('access')
        logger.info(
            f"Request started: {request.method} {request.url} "
            f"from {request.remote_addr}"
        )

def log_request_end(response):
    """Log the end of each request with response details."""
    if has_request_context():
        logger = logging.getLogger('access')
        logger.info(
            f"Request completed: {request.method} {request.url} "
            f"Status: {response.status_code} "
            f"Size: {len(response.get_data())} bytes"
        )
    return response

def log_security_event(event_type, details, user_id=None, ip_address=None):
    """Log security-related events."""
    logger = logging.getLogger('security')
    logger.warning(
        f"Security event: {event_type} - {details} "
        f"User: {user_id or 'unknown'} "
        f"IP: {ip_address or 'unknown'}"
    )

def log_error(error, context=None):
    """Log errors with context."""
    logger = logging.getLogger('errors')
    logger.error(
        f"Error occurred: {str(error)} "
        f"Context: {context or 'none'} "
        f"Type: {type(error).__name__}"
    )

def log_performance(operation, duration, details=None):
    """Log performance metrics."""
    logger = logging.getLogger('performance')
    logger.info(
        f"Performance: {operation} took {duration:.3f}s "
        f"Details: {details or 'none'}"
    )

def log_ai_interaction(interaction_type, user_id, details=None):
    """Log AI-related interactions."""
    logger = logging.getLogger('ai')
    logger.info(
        f"AI interaction: {interaction_type} "
        f"User: {user_id} "
        f"Details: {details or 'none'}"
    )

def log_memory_operation(operation, user_id, details=None):
    """Log memory system operations."""
    logger = logging.getLogger('memory')
    logger.info(
        f"Memory operation: {operation} "
        f"User: {user_id} "
        f"Details: {details or 'none'}"
    )

def log_database_operation(operation, table, user_id=None, details=None):
    """Log database operations."""
    logger = logging.getLogger('database')
    logger.info(
        f"Database operation: {operation} "
        f"Table: {table} "
        f"User: {user_id or 'system'} "
        f"Details: {details or 'none'}"
    )

def log_authentication_event(event_type, user_id, ip_address, success, details=None):
    """Log authentication events."""
    logger = logging.getLogger('auth')
    level = logging.INFO if success else logging.WARNING
    logger.log(
        level,
        f"Authentication: {event_type} "
        f"User: {user_id} "
        f"IP: {ip_address} "
        f"Success: {success} "
        f"Details: {details or 'none'}"
    )

def log_rate_limit_event(user_id, ip_address, endpoint, limit_exceeded):
    """Log rate limiting events."""
    logger = logging.getLogger('rate_limit')
    level = logging.WARNING if limit_exceeded else logging.DEBUG
    logger.log(
        level,
        f"Rate limit: Endpoint: {endpoint} "
        f"User: {user_id or 'anonymous'} "
        f"IP: {ip_address} "
        f"Limit exceeded: {limit_exceeded}"
    )

def log_content_filter_event(user_id, content, filter_result, details=None):
    """Log content filtering events."""
    logger = logging.getLogger('content_filter')
    level = logging.WARNING if filter_result.get('blocked') else logging.INFO
    logger.log(
        level,
        f"Content filter: User: {user_id} "
        f"Blocked: {filter_result.get('blocked', False)} "
        f"Warnings: {len(filter_result.get('warnings', []))} "
        f"Details: {details or 'none'}"
    )

def get_logger(name):
    """Get a logger with the specified name."""
    return logging.getLogger(name)
