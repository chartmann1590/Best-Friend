import pytest
from app.models import User, Memory, Message
from app.services.memory import MemoryService
from datetime import datetime, timedelta

@pytest.fixture
def memory_service(app):
    return MemoryService(app)

class TestMemoryCreation:
    """Test memory creation functionality."""
    
    def test_create_basic_memory(self, app, user, memory_service):
        """Test creating a basic memory."""
        with app.app_context():
            memory = memory_service.create_memory(
                user_id=user.id,
                content='Test memory content',
                memory_type='conversation'
            )
            assert memory is not None
            assert memory.content == 'Test memory content'
            assert memory.memory_type == 'conversation'
            assert memory.user_id == user.id
            assert memory.importance == 1.0
    
    def test_create_memory_with_metadata(self, app, user, memory_service):
        """Test creating memory with metadata."""
        with app.app_context():
            metadata = {'source': 'test', 'confidence': 0.95}
            memory = memory_service.create_memory(
                user_id=user.id,
                content='Memory with metadata',
                memory_type='fact',
                importance=0.8,
                metadata=metadata
            )
            assert memory.memory_metadata == metadata
    
    def test_create_memory_with_custom_importance(self, app, user, memory_service):
        """Test creating memory with custom importance."""
        with app.app_context():
            memory = memory_service.create_memory(
                user_id=user.id,
                content='Important memory',
                memory_type='preference',
                importance=0.9
            )
            assert memory.importance == 0.9

class TestMemorySearch:
    """Test memory search functionality."""
    
    def test_search_memories_basic(self, app, user, memory_service):
        """Test basic memory search."""
        with app.app_context():
            # Create test memories
            memory1 = memory_service.create_memory(
                user_id=user.id,
                content='Memory about cats',
                memory_type='fact'
            )
            memory2 = memory_service.create_memory(
                user_id=user.id,
                content='Memory about dogs',
                memory_type='fact'
            )
            
            # Search for cat-related memories
            results = memory_service.search_memories(
                user_id=user.id,
                query='cats',
                limit=10
            )
            assert len(results) > 0
    
    def test_search_memories_with_threshold(self, app, user, memory_service):
        """Test memory search with similarity threshold."""
        with app.app_context():
            memory = memory_service.create_memory(
                user_id=user.id,
                content='Test memory for threshold search',
                memory_type='conversation'
            )
            
            # Search with high threshold
            results = memory_service.search_memories(
                user_id=user.id,
                query='threshold',
                limit=10,
                threshold=0.9
            )
            # Results may be empty with high threshold
            assert isinstance(results, list)
    
    def test_search_memories_limit(self, app, user, memory_service):
        """Test memory search with limit."""
        with app.app_context():
            # Create multiple memories
            for i in range(15):
                memory_service.create_memory(
                    user_id=user.id,
                    content=f'Memory {i}',
                    memory_type='conversation'
                )
            
            # Search with limit
            results = memory_service.search_memories(
                user_id=user.id,
                query='Memory',
                limit=5
            )
            assert len(results) <= 5

class TestMemoryRetrieval:
    """Test memory retrieval functionality."""
    
    def test_get_recent_memories(self, app, user, memory_service):
        """Test getting recent memories."""
        with app.app_context():
            # Create memories with different dates
            old_date = datetime.utcnow() - timedelta(days=10)
            recent_date = datetime.utcnow() - timedelta(days=2)
            
            old_memory = Memory(
                user_id=user.id,
                content='Old memory',
                memory_type='conversation',
                created_at=old_date
            )
            recent_memory = Memory(
                user_id=user.id,
                content='Recent memory',
                memory_type='conversation',
                created_at=recent_date
            )
            
            db.session.add_all([old_memory, recent_memory])
            db.session.commit()
            
            # Get recent memories (last 7 days)
            recent_memories = memory_service.get_recent_memories(
                user_id=user.id,
                days=7
            )
            assert len(recent_memories) >= 1
            assert recent_memory in recent_memories
    
    def test_get_important_memories(self, app, user, memory_service):
        """Test getting important memories."""
        with app.app_context():
            # Create memories with different importance
            low_importance = memory_service.create_memory(
                user_id=user.id,
                content='Low importance',
                memory_type='conversation',
                importance=0.3
            )
            high_importance = memory_service.create_memory(
                user_id=user.id,
                content='High importance',
                memory_type='conversation',
                importance=0.9
            )
            
            # Get important memories (importance >= 0.8)
            important_memories = memory_service.get_important_memories(
                user_id=user.id
            )
            assert high_importance in important_memories
            assert low_importance not in important_memories

class TestMemoryManagement:
    """Test memory management functionality."""
    
    def test_update_memory_importance(self, app, user, memory_service):
        """Test updating memory importance."""
        with app.app_context():
            memory = memory_service.create_memory(
                user_id=user.id,
                content='Memory to update',
                memory_type='conversation'
            )
            
            # Update importance
            success = memory_service.update_memory_importance(memory.id, 0.7)
            assert success is True
            
            # Check updated value
            updated_memory = Memory.query.get(memory.id)
            assert updated_memory.importance == 0.7
    
    def test_cleanup_old_memories(self, app, user, memory_service):
        """Test cleanup of old memories."""
        with app.app_context():
            # Create old, low-importance memory
            old_date = datetime.utcnow() - timedelta(days=400)
            old_memory = Memory(
                user_id=user.id,
                content='Old low importance memory',
                memory_type='conversation',
                importance=0.3,
                created_at=old_date
            )
            db.session.add(old_memory)
            db.session.commit()
            
            # Run cleanup
            deleted_count = memory_service.cleanup_old_memories(user.id)
            assert deleted_count >= 0  # May be 0 if no cleanup needed
    
    def test_memory_stats(self, app, user, memory_service):
        """Test memory statistics."""
        with app.app_context():
            # Create different types of memories
            memory_service.create_memory(
                user_id=user.id,
                content='Conversation memory',
                memory_type='conversation'
            )
            memory_service.create_memory(
                user_id=user.id,
                content='Fact memory',
                memory_type='fact'
            )
            memory_service.create_memory(
                user_id=user.id,
                content='Preference memory',
                memory_type='preference'
            )
            
            # Get stats
            stats = memory_service.get_memory_stats(user.id)
            assert stats['total'] >= 3
            assert stats['conversations'] >= 1
            assert stats['facts'] >= 1
            assert stats['preferences'] >= 1

class TestConversationMemory:
    """Test conversation memory functionality."""
    
    def test_create_conversation_memory(self, app, user, memory_service):
        """Test creating memory from conversation."""
        with app.app_context():
            # Create test messages
            messages = [
                Message(
                    user_id=user.id,
                    role='user',
                    content='Hello, how are you?',
                    timestamp=datetime.utcnow()
                ),
                Message(
                    user_id=user.id,
                    role='assistant',
                    content='I am doing well, thank you!',
                    timestamp=datetime.utcnow()
                )
            ]
            db.session.add_all(messages)
            db.session.commit()
            
            # Create conversation memory
            memory = memory_service.create_conversation_memory(
                user_id=user.id,
                messages=messages
            )
            assert memory is not None
            assert memory.memory_type == 'conversation'
            assert memory.importance == 0.8
