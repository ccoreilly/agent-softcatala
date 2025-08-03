"""
Simple pytest configuration with minimal, targeted mocking.
Focus on useful fixtures rather than comprehensive import mocking.
"""
import pytest
import os
import sys
from unittest.mock import patch
from datetime import datetime


# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    env_vars = {
        'OPENAI_API_KEY': 'test-openai-key',
        'ANTHROPIC_API_KEY': 'test-anthropic-key', 
        'ZHIPU_API_KEY': 'test-zhipu-key',
        'OLLAMA_BASE_URL': 'http://localhost:11434',
        'LOG_LEVEL': 'INFO',
    }
    
    with patch.dict('os.environ', env_vars):
        yield env_vars


@pytest.fixture
def sample_chat_messages():
    """Sample chat messages for testing."""
    return [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "Can you help me with a task?"}
    ]


@pytest.fixture  
def sample_model_response():
    """Sample model response for testing."""
    return {
        "id": "test-response-123",
        "object": "chat.completion", 
        "created": 1234567890,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response from the model."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 20,
            "completion_tokens": 10,
            "total_tokens": 30
        }
    }


@pytest.fixture
def sample_health_response():
    """Sample health check response."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "agent": {"status": "healthy", "model": "test-model"},
            "providers": {"status": "healthy", "available": ["openai", "anthropic"]},
            "tools": {"status": "healthy", "count": 3}
        },
        "system": {
            "memory_usage": 45.2,
            "cpu_usage": 12.8,
            "uptime": "2h 30m"  
        }
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test") 
    config.addinivalue_line("markers", "slow: mark test as slow")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add integration marker to tests with "integration" in the name
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        # Add unit marker to tests with "unit" in the name  
        elif "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)