import pytest
from app.models import User, Setting
from app.services.security import SecurityService
import json

@pytest.fixture
def security_service(app):
    return SecurityService(app)

class TestSettingsModel:
    """Test Setting model functionality."""
    
    def test_create_setting(self, app, user):
        """Test creating a basic setting."""
        with app.app_context():
            setting = Setting(
                user_id=user.id,
                key='test_key',
                value='test_value',
                is_encrypted=False
            )
            db.session.add(setting)
            db.session.commit()
            
            assert setting.id is not None
            assert setting.key == 'test_key'
            assert setting.value == 'test_value'
            assert setting.is_encrypted is False
    
    def test_setting_unique_constraint(self, app, user):
        """Test that user_id + key combination is unique."""
        with app.app_context():
            # Create first setting
            setting1 = Setting(
                user_id=user.id,
                key='unique_key',
                value='value1'
            )
            db.session.add(setting1)
            db.session.commit()
            
            # Try to create duplicate
            setting2 = Setting(
                user_id=user.id,
                key='unique_key',
                value='value2'
            )
            db.session.add(setting2)
            
            # Should raise integrity error
            with pytest.raises(Exception):
                db.session.commit()
    
    def test_setting_timestamps(self, app, user):
        """Test setting timestamp fields."""
        with app.app_context():
            setting = Setting(
                user_id=user.id,
                key='timestamp_test',
                value='test'
            )
            db.session.add(setting)
            db.session.commit()
            
            assert setting.created_at is not None
            assert setting.updated_at is not None

class TestSettingsEncryption:
    """Test settings encryption functionality."""
    
    def test_encrypt_setting(self, app, user, security_service):
        """Test encrypting a setting value."""
        with app.app_context():
            setting = Setting(
                user_id=user.id,
                key='encrypted_key',
                value='sensitive_value',
                is_encrypted=True
            )
            
            # Encrypt the value
            encrypted_value = security_service.encrypt_value(setting.value)
            setting.value = encrypted_value
            
            db.session.add(setting)
            db.session.commit()
            
            # Verify value is encrypted
            assert setting.value != 'sensitive_value'
            assert len(setting.value) > len('sensitive_value')
    
    def test_decrypt_setting(self, app, user, security_service):
        """Test decrypting a setting value."""
        with app.app_context():
            original_value = 'sensitive_value'
            encrypted_value = security_service.encrypt_value(original_value)
            
            setting = Setting(
                user_id=user.id,
                key='decrypt_test',
                value=encrypted_value,
                is_encrypted=True
            )
            db.session.add(setting)
            db.session.commit()
            
            # Decrypt the value
            decrypted_value = security_service.decrypt_value(setting.value)
            assert decrypted_value == original_value
    
    def test_setting_encryption_methods(self, app, user):
        """Test Setting model encryption methods."""
        with app.app_context():
            setting = Setting(
                user_id=user.id,
                key='method_test',
                value='test_value',
                is_encrypted=True
            )
            
            # Test set_value method
            setting.set_value('new_value')
            assert setting.value != 'new_value'  # Should be encrypted
            
            # Test get_value method
            retrieved_value = setting.get_value()
            assert retrieved_value == 'new_value'

class TestSettingsCRUD:
    """Test settings CRUD operations."""
    
    def test_create_setting(self, app, user):
        """Test creating a setting."""
        with app.app_context():
            setting = Setting(
                user_id=user.id,
                key='create_test',
                value='create_value'
            )
            db.session.add(setting)
            db.session.commit()
            
            # Verify it was created
            retrieved = Setting.query.filter_by(
                user_id=user.id,
                key='create_test'
            ).first()
            assert retrieved is not None
            assert retrieved.value == 'create_value'
    
    def test_read_setting(self, app, user):
        """Test reading a setting."""
        with app.app_context():
            setting = Setting(
                user_id=user.id,
                key='read_test',
                value='read_value'
            )
            db.session.add(setting)
            db.session.commit()
            
            # Read the setting
            retrieved = Setting.query.filter_by(
                user_id=user.id,
                key='read_test'
            ).first()
            assert retrieved.value == 'read_value'
    
    def test_update_setting(self, app, user):
        """Test updating a setting."""
        with app.app_context():
            setting = Setting(
                user_id=user.id,
                key='update_test',
                value='old_value'
            )
            db.session.add(setting)
            db.session.commit()
            
            # Update the setting
            setting.value = 'new_value'
            db.session.commit()
            
            # Verify update
            retrieved = Setting.query.filter_by(
                user_id=user.id,
                key='update_test'
            ).first()
            assert retrieved.value == 'new_value'
    
    def test_delete_setting(self, app, user):
        """Test deleting a setting."""
        with app.app_context():
            setting = Setting(
                user_id=user.id,
                key='delete_test',
                value='delete_value'
            )
            db.session.add(setting)
            db.session.commit()
            
            # Delete the setting
            db.session.delete(setting)
            db.session.commit()
            
            # Verify deletion
            retrieved = Setting.query.filter_by(
                user_id=user.id,
                key='delete_test'
            ).first()
            assert retrieved is None

class TestSettingsValidation:
    """Test settings validation."""
    
    def test_setting_key_validation(self, app, user):
        """Test setting key validation."""
        with app.app_context():
            # Test empty key
            with pytest.raises(Exception):
                setting = Setting(
                    user_id=user.id,
                    key='',
                    value='test'
                )
                db.session.add(setting)
                db.session.commit()
    
    def test_setting_value_validation(self, app, user):
        """Test setting value validation."""
        with app.app_context():
            # Test None value (should be allowed)
            setting = Setting(
                user_id=user.id,
                key='none_value_test',
                value=None
            )
            db.session.add(setting)
            db.session.commit()
            
            assert setting.value is None

class TestSettingsSerialization:
    """Test settings serialization."""
    
    def test_setting_to_dict(self, app, user):
        """Test converting setting to dictionary."""
        with app.app_context():
            setting = Setting(
                user_id=user.id,
                key='serialize_test',
                value='serialize_value',
                is_encrypted=False
            )
            db.session.add(setting)
            db.session.commit()
            
            # Convert to dict
            setting_dict = setting.to_dict()
            
            assert 'id' in setting_dict
            assert 'user_id' in setting_dict
            assert 'key' in setting_dict
            assert 'value' in setting_dict
            assert 'is_encrypted' in setting_dict
            assert 'created_at' in setting_dict
            assert 'updated_at' in setting_dict
    
    def test_setting_json_serialization(self, app, user):
        """Test JSON serialization of settings."""
        with app.app_context():
            setting = Setting(
                user_id=user.id,
                key='json_test',
                value='json_value'
            )
            db.session.add(setting)
            db.session.commit()
            
            # Test JSON serialization
            setting_dict = setting.to_dict()
            json_str = json.dumps(setting_dict)
            parsed = json.loads(json_str)
            
            assert parsed['key'] == 'json_test'
            assert parsed['value'] == 'json_value'

class TestSettingsQueries:
    """Test settings queries."""
    
    def test_get_user_settings(self, app, user):
        """Test getting all settings for a user."""
        with app.app_context():
            # Create multiple settings
            settings_data = [
                ('key1', 'value1'),
                ('key2', 'value2'),
                ('key3', 'value3')
            ]
            
            for key, value in settings_data:
                setting = Setting(
                    user_id=user.id,
                    key=key,
                    value=value
                )
                db.session.add(setting)
            db.session.commit()
            
            # Query all settings for user
            user_settings = Setting.query.filter_by(user_id=user.id).all()
            assert len(user_settings) == 3
            
            # Verify all keys are present
            keys = [s.key for s in user_settings]
            assert 'key1' in keys
            assert 'key2' in keys
            assert 'key3' in keys
    
    def test_get_setting_by_key(self, app, user):
        """Test getting a specific setting by key."""
        with app.app_context():
            setting = Setting(
                user_id=user.id,
                key='specific_key',
                value='specific_value'
            )
            db.session.add(setting)
            db.session.commit()
            
            # Query by key
            retrieved = Setting.query.filter_by(
                user_id=user.id,
                key='specific_key'
            ).first()
            
            assert retrieved is not None
            assert retrieved.value == 'specific_value'
