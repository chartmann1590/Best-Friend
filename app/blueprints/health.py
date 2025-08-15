from flask import Blueprint, jsonify
from app import db
import redis
import requests
from app.config import Config

health_bp = Blueprint('health', __name__)

@health_bp.route('/')
def health_check():
    """Health check endpoint."""
    status = {
        'status': 'healthy',
        'services': {}
    }
    
    # Check database
    try:
        db.session.execute('SELECT 1')
        status['services']['database'] = 'healthy'
    except Exception as e:
        status['services']['database'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    # Check Redis
    try:
        r = redis.from_url(Config.REDIS_URL)
        r.ping()
        status['services']['redis'] = 'healthy'
    except Exception as e:
        status['services']['redis'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    # Check Ollama
    try:
        response = requests.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            status['services']['ollama'] = 'healthy'
        else:
            status['services']['ollama'] = f'unhealthy: HTTP {response.status_code}'
            status['status'] = 'unhealthy'
    except Exception as e:
        status['services']['ollama'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    # Check TTS
    try:
        response = requests.get(f"{Config.TTS_URL}/api/voices", timeout=5)
        if response.status_code == 200:
            status['services']['tts'] = 'healthy'
        else:
            status['services']['tts'] = f'unhealthy: HTTP {response.status_code}'
            status['status'] = 'unhealthy'
    except Exception as e:
        status['services']['tts'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    return jsonify(status)
