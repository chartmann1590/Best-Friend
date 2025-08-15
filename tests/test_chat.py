import pytest
from flask import url_for
from app import create_app, db
from app.models import User, Message, Memory
from app.services.memory import MemoryService
from app.services.ollama_client import OllamaClient
import json

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def user(app):
    user = User(
        email='test@example.com',
        name='Test User',
        is_active=True
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def authenticated_client(client, user):
    with client.session_transaction() as sess:
        sess['user_id'] = user.id
    return client

class TestChatAPI:
    """Test chat API endpoints."""
    
    def test_chat_endpoint_requires_auth(self, client):
        """Test that chat endpoint requires authentication."""
        response = client.post('/api/chat', json={'message': 'Hello'})
        assert response.status_code == 401
    
    def test_chat_endpoint_with_auth(self, authenticated_client, app):
        """Test chat endpoint with valid authentication."""
        with app.app_context():
            response = authenticated_client.post('/api/chat', json={'message': 'Hello'})
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'response' in data
            assert 'message_id' in data
    
    def test_chat_message_storage(self, authenticated_client, app, user):
        """Test that chat messages are stored in database."""
        with app.app_context():
            response = authenticated_client.post('/api/chat', json={'message': 'Test message'})
            assert response.status_code == 200
            
            # Check message was stored
            message = Message.query.filter_by(user_id=user.id, role='user').first()
            assert message is not None
            assert message.content == 'Test message'
    
    def test_stt_endpoint_requires_auth(self, client):
        """Test that STT endpoint requires authentication."""
        response = client.post('/api/stt')
        assert response.status_code == 401
    
    def test_tts_endpoint_requires_auth(self, client):
        """Test that TTS endpoint requires authentication."""
        response = client.get('/api/tts/stream?text=Hello')
        assert response.status_code == 401
    
    def test_memory_search_requires_auth(self, client):
        """Test that memory search requires authentication."""
        response = client.get('/api/memory/search?q=test')
        assert response.status_code == 401

class TestMemorySystem:
    """Test memory system functionality."""
    
    def test_memory_creation(self, app, user):
        """Test memory creation and storage."""
        with app.app_context():
            memory_service = MemoryService(app)
            memory = memory_service.create_memory(
                user_id=user.id,
                content='Test memory content',
                memory_type='conversation'
            )
            assert memory is not None
            assert memory.content == 'Test memory content'
            assert memory.user_id == user.id
    
    def test_memory_search(self, app, user):
        """Test memory search functionality."""
        with app.app_context():
            # Create test memory
            memory_service = MemoryService(app)
            memory = memory_service.create_memory(
                user_id=user.id,
                content='Test memory for search',
                memory_type='conversation'
            )
            
            # Search for memory
            results = memory_service.search_memories(
                user_id=user.id,
                query='search',
                limit=10
            )
            assert len(results) > 0
            assert results[0][0].id == memory.id
    
    def test_memory_importance_scoring(self, app, user):
        """Test memory importance scoring."""
        with app.app_context():
            memory_service = MemoryService(app)
            memory = memory_service.create_memory(
                user_id=user.id,
                content='Important memory',
                memory_type='fact',
                importance=0.9
            )
            
            # Update importance
            success = memory_service.update_memory_importance(memory.id, 0.8)
            assert success is True
            
            # Check updated importance
            updated_memory = Memory.query.get(memory.id)
            assert updated_memory.importance == 0.8

class TestOllamaIntegration:
    """Test Ollama client integration."""
    
    def test_ollama_client_initialization(self, app):
        """Test Ollama client initialization."""
        with app.app_context():
            client = OllamaClient(app)
            assert client.base_url == 'http://localhost:11434'
            assert client.default_model == 'llama3.1:8b'
    
    def test_ollama_health_check(self, app):
        """Test Ollama health check."""
        with app.app_context():
            client = OllamaClient(app)
            # This will fail without actual Ollama server, but should not crash
            health = client.health_check()
            assert isinstance(health, bool)
    
    def test_ollama_model_listing(self, app):
        """Test Ollama model listing."""
        with app.app_context():
            client = OllamaClient(app)
            models = client.list_models()
            assert isinstance(models, list)

class TestChatUI:
    """Test chat UI functionality."""
    
    def test_chat_page_requires_auth(self, client):
        """Test that chat page requires authentication."""
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login
    
    def test_chat_page_with_auth(self, authenticated_client):
        """Test chat page with valid authentication."""
        response = authenticated_client.get('/')
        assert response.status_code == 200
        assert b'chatMessages' in response.data
    
    def test_onboarding_page_access(self, client):
        """Test onboarding page access."""
        response = client.get('/onboarding')
        assert response.status_code == 200
        assert b'onboarding' in response.data.lower()
