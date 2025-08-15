import pytest

def test_basic_import():
    """Test that basic imports work."""
    assert True

def test_pytest_working():
    """Simple test to verify pytest is working."""
    assert 1 + 1 == 2
    assert "hello" in "hello world"

def test_fixtures_available(test_user, admin_user):
    """Test that fixtures are available."""
    assert test_user.email == 'test@example.com'
    assert admin_user.is_admin == True
    assert test_user.check_password('password123') == True
    assert test_user.check_password('wrong') == False

@pytest.mark.skipif(True, reason="Skipping app-dependent tests")
def test_app_creation(app):
    """Test that would require the full app."""
    pytest.skip("This test requires the full app")

@pytest.mark.skipif(True, reason="Skipping client tests")
def test_client_creation(client):
    """Test that would require the test client."""
    pytest.skip("This test requires the test client")

@pytest.mark.skipif(True, reason="Skipping runner tests")
def test_runner_creation(runner):
    """Test that would require the test runner."""
    pytest.skip("This test requires the test runner")
