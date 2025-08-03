"""
Pytest configuration and shared fixtures
"""
import pytest
import os
import sys
from unittest.mock import patch

# Add backend directory to Python path for all tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(autouse=True)
def mock_environment():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'CORS_ORIGINS': 'http://localhost:3000,http://localhost:3001',
        'TELEGRAM_BOT_TOKEN': '',  # Ensure no telegram bot in tests
        'ZHIPU_API_KEY': 'test-key',
        'OLLAMA_BASE_URL': 'http://localhost:11434',
    }, clear=False):
        yield


@pytest.fixture
def sample_chat_messages():
    """Sample chat messages for testing."""
    return [
        {"role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:00"},
        {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01T00:00:01"},
        {"role": "user", "content": "How are you?", "timestamp": "2024-01-01T00:00:02"}
    ]


@pytest.fixture
def sample_model_response():
    """Sample model response for testing."""
    return {
        "status": "available",
        "available_models": ["llama3.1", "mistral", "glm-4"],
        "response_time": 0.25
    }


@pytest.fixture
def sample_health_response():
    """Sample health check response for testing."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00",
        "models": {
            "ollama": {
                "status": "available",
                "available_models": ["llama3.1", "mistral"]
            },
            "zhipu": {
                "status": "available", 
                "available_models": ["glm-4", "glm-3-turbo"]
            }
        },
        "tools": {
            "count": 3,
            "names": ["web_browser", "search", "wikipedia"]
        }
    }


# Configure asyncio event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )