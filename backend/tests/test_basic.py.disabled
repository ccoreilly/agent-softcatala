"""
Basic tests to verify test infrastructure works
"""
import pytest
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_basic_functionality():
    """Test that basic Python functionality works."""
    assert 1 + 1 == 2
    assert "hello" == "hello"
    assert [1, 2, 3] == [1, 2, 3]


def test_imports_work():
    """Test that basic imports work."""
    import json
    import os
    import sys
    
    assert json.dumps({"test": True}) == '{"test": true}'
    assert os.path.exists(".")
    assert sys.version_info.major >= 3


def test_fastapi_basic():
    """Test that FastAPI can be imported and basic app creation works."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    # Create a simple test app
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}
    
    # Test with client
    client = TestClient(app)
    response = client.get("/test")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_async_functionality():
    """Test that async functionality works."""
    async def async_func():
        return "async_result"
    
    result = await async_func()
    assert result == "async_result"


def test_pytest_fixtures():
    """Test that pytest fixtures work."""
    # This test uses the mock_environment fixture from conftest.py
    import os
    
    # Should have our mocked environment variables
    cors_origins = os.getenv("CORS_ORIGINS")
    assert cors_origins is not None
    assert "localhost:3000" in cors_origins


class TestBasicClass:
    """Test class-based tests work."""
    
    def test_class_method(self):
        """Test that class-based test methods work."""
        assert True
    
    def test_setup_works(self):
        """Test that test setup works correctly.""" 
        # This should run with our conftest.py fixtures
        assert os.getenv("TELEGRAM_BOT_TOKEN") == ""  # Should be empty from our mock