"""
Pytest configuration and shared fixtures for backend tests.
This module provides comprehensive mocking for external dependencies.
"""

import sys
import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, Any, List
from datetime import datetime


# =============================================================================
# MODULE-LEVEL MOCKING - Prevents import errors
# =============================================================================

class MockLangChainModule(Mock):
    """Mock for langchain modules that provides common LangChain interfaces."""
    
    def __getattr__(self, name):
        if name == 'AgentExecutor':
            return MockAgentExecutor
        elif name == 'create_openai_tools_agent':
            return Mock()
        elif name.endswith('Tool'):
            return MockBaseTool
        elif name == 'ChatOllama':
            return Mock
        elif name == 'chat_models':
            return MockChatModels()
        else:
            return Mock()

class MockChatModels:
    """Mock for langchain_community.chat_models."""
    ChatZhipuAI = Mock
    ChatOllama = Mock

class MockLangChainCore(Mock):
    """Mock for langchain_core modules."""
    
    def __getattr__(self, name):
        if name == 'messages':
            return MockMessages()
        elif name == 'tools':
            return MockTools()
        elif name == 'callbacks':
            return MockCallbacks()
        elif name == 'prompts':
            return MockPrompts()
        elif name == 'runnables':
            return MockRunnables()
        elif name == 'language_models':
            return MockLanguageModels()
        else:
            return Mock()

class MockMessages:
    """Mock for langchain_core.messages."""
    HumanMessage = Mock
    AIMessage = Mock
    SystemMessage = Mock

class MockTools:
    """Mock for langchain_core.tools."""
    BaseTool = Mock

class MockCallbacks:
    """Mock for langchain_core.callbacks."""
    AsyncCallbackHandler = Mock
    CallbackManagerForToolRun = Mock
    AsyncCallbackManagerForToolRun = Mock

class MockPrompts:
    """Mock for langchain_core.prompts."""
    ChatPromptTemplate = Mock
    MessagesPlaceholder = Mock

class MockRunnables:
    """Mock for langchain_core.runnables."""
    RunnableConfig = Mock

class MockLanguageModels:
    """Mock for langchain_core.language_models."""
    class base:
        BaseLanguageModel = Mock
    
    class chat_models:
        BaseChatModel = Mock

class MockAgentExecutor(Mock):
    """Mock for LangChain AgentExecutor."""
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.agent = Mock()
        self.tools = kwargs.get('tools', [])
    
    async def astream(self, *args, **kwargs):
        """Mock async streaming."""
        yield {"output": "Mocked response"}

class MockBaseTool(Mock):
    """Mock for LangChain BaseTool."""
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.name = kwargs.get('name', 'mock_tool')
        self.description = kwargs.get('description', 'Mock tool')

class MockLangChainAgent(Mock):
    """Comprehensive mock for LangChainAgent class."""
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.current_model = "mock-model"
        self.tools = kwargs.get('tools', [])
        self.provider = "mock-provider"
    
    async def check_health(self):
        return {"status": "healthy", "model": self.current_model}
    
    async def get_available_models(self):
        return ["mock-model-1", "mock-model-2"]
    
    def switch_model(self, model_name: str, provider: str = None):
        self.current_model = model_name
        if provider:
            self.provider = provider
        return True
    
    async def chat_stream(self, messages: List[Dict[str, Any]], **kwargs):
        """Mock chat streaming."""
        for i, chunk in enumerate(["Hello", " ", "world", "!"]):
            yield {
                "type": "token",
                "content": chunk,
                "metadata": {"index": i}
            }

class MockFastAPI(Mock):
    """Mock FastAPI app with all expected routes."""
    
    def __init__(self):
        super().__init__()
        self.routes = []
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup mock routes that match our API."""
        routes = [
            "/", "/health", "/models", "/models/switch", 
            "/tools", "/providers", "/chat/stream"
        ]
        for route in routes:
            self.routes.append(Mock(path=route))
    
    def get(self, path):
        def decorator(func):
            return func
        return decorator
    
    def post(self, path):
        def decorator(func):
            return func
        return decorator

# Mock all the problematic modules BEFORE they get imported
mock_modules = {
    'langchain': MockLangChainModule(),
    'langchain.agents': MockLangChainModule(),
    'langchain_core': MockLangChainCore(),
    'langchain_core.messages': MockMessages(),
    'langchain_core.tools': MockTools(),
    'langchain_core.callbacks': MockCallbacks(),
    'langchain_core.prompts': MockPrompts(),
    'langchain_core.runnables': MockRunnables(),
    'langchain_core.language_models': MockLanguageModels(),
    'langchain_core.language_models.base': MockLanguageModels.base(),
    'langchain_core.language_models.chat_models': MockLanguageModels.chat_models(),
    'langchain_ollama': Mock(),
    'langchain_community': MockLangChainModule(),
    'langchain_community.chat_models': MockChatModels(),
    'langchain_community.tools': Mock(),
    'chromadb': Mock(),
    'zhipuai': Mock(),
    'ollama': Mock(),
    'selenium': Mock(),
    'selenium.webdriver': Mock(),
    'webdriver_manager': Mock(),
    'webdriver_manager.chrome': Mock(),
}

# Install mocks in sys.modules
for module_name, mock_module in mock_modules.items():
    if module_name not in sys.modules:
        sys.modules[module_name] = mock_module


# =============================================================================
# PYTEST FIXTURES
# =============================================================================

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

@pytest.fixture
def mock_langchain_agent():
    """Fixture providing a mocked LangChain agent."""
    return MockLangChainAgent()

@pytest.fixture
def mock_fastapi_app():
    """Fixture providing a mocked FastAPI app."""
    return MockFastAPI()

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# =============================================================================
# AUTOUSE FIXTURES - Applied automatically to all tests
# =============================================================================

# Removed autouse fixture - it was causing import issues
# Tests can use individual fixtures or the mock_langchain_agent fixture as needed


# Add backend directory to Python path for all tests
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


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