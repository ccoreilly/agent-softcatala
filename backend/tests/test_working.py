"""
Working tests that can run successfully with our mocking setup.
Focus on functionality we can test without complex import chains.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json


def test_basic_imports():
    """Test that basic LangChain imports work."""
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_core.tools import BaseTool
    from langchain_core.callbacks import AsyncCallbackHandler
    
    # These should be mocked and importable
    assert HumanMessage is not None
    assert AIMessage is not None
    assert BaseTool is not None
    assert AsyncCallbackHandler is not None


def test_mock_langchain_agent_functionality(mock_langchain_agent):
    """Test our mocked LangChain agent works as expected."""
    # Test basic attributes
    assert hasattr(mock_langchain_agent, 'current_model')
    assert hasattr(mock_langchain_agent, 'tools')
    assert hasattr(mock_langchain_agent, 'provider')
    
    # Test model switching
    result = mock_langchain_agent.switch_model('new-model', 'new-provider')
    assert result is True
    assert mock_langchain_agent.current_model == 'new-model'
    assert mock_langchain_agent.provider == 'new-provider'


@pytest.mark.asyncio
async def test_mock_agent_async_methods(mock_langchain_agent):
    """Test async methods of our mocked agent."""
    # Test health check
    health = await mock_langchain_agent.check_health()
    assert health['status'] == 'healthy'
    assert health['model'] == mock_langchain_agent.current_model
    
    # Test model listing
    models = await mock_langchain_agent.get_available_models()
    assert isinstance(models, list)
    assert 'mock-model-1' in models
    assert 'mock-model-2' in models


@pytest.mark.asyncio
async def test_mock_chat_streaming(mock_langchain_agent):
    """Test chat streaming functionality."""
    messages = [{"role": "user", "content": "Hello"}]
    
    chunks = []
    async for chunk in mock_langchain_agent.chat_stream(messages):
        chunks.append(chunk)
        
    # Should get 4 chunks: "Hello", " ", "world", "!"
    assert len(chunks) == 4
    assert all('content' in chunk for chunk in chunks)
    assert all('type' in chunk for chunk in chunks)
    assert all('metadata' in chunk for chunk in chunks)
    
    # Reconstruct the message
    content = ''.join(chunk['content'] for chunk in chunks)
    assert content == "Hello world!"


def test_fastapi_mock_app():
    """Test that we can create a mock FastAPI app for testing."""
    app = FastAPI()
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "timestamp": "2024-01-01T00:00:00"}
    
    @app.get("/models")
    async def get_models():
        return {"models": ["mock-model-1", "mock-model-2"]}
    
    @app.post("/chat/stream")
    async def chat_stream(request: dict):
        return {"response": "Mock response"}
    
    client = TestClient(app)
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    
    # Test models endpoint
    response = client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 2
    
    # Test chat endpoint
    response = client.post("/chat/stream", json={"message": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data


def test_mock_fixtures_work(mock_environment, sample_chat_messages, sample_health_response):
    """Test that our fixtures work properly."""
    # Test environment fixture
    assert mock_environment['OPENAI_API_KEY'] == 'test-openai-key'
    assert mock_environment['ZHIPU_API_KEY'] == 'test-zhipu-key'
    
    # Test chat messages fixture
    assert len(sample_chat_messages) == 3
    assert sample_chat_messages[0]['role'] == 'user'
    assert sample_chat_messages[1]['role'] == 'assistant'
    
    # Test health response fixture
    assert sample_health_response['status'] == 'healthy'
    assert 'services' in sample_health_response
    assert 'system' in sample_health_response


@pytest.mark.asyncio
async def test_mock_agent_with_tools():
    """Test agent functionality with mock tools."""
    from tests.conftest import MockLangChainAgent
    
    # Create agent with mock tools
    tool1 = Mock()
    tool1.name = "tool1"
    tool2 = Mock()  
    tool2.name = "tool2"
    mock_tools = [tool1, tool2]
    agent = MockLangChainAgent(tools=mock_tools)
    
    assert len(agent.tools) == 2
    assert agent.tools[0].name == "tool1"
    assert agent.tools[1].name == "tool2"
    
    # Test that agent methods still work
    health = await agent.check_health()
    assert health['status'] == 'healthy'


def test_pydantic_models_work():
    """Test that Pydantic models work for request/response validation."""
    from pydantic import BaseModel
    from typing import List
    
    class ChatMessage(BaseModel):
        role: str
        content: str
    
    class ChatRequest(BaseModel):
        messages: List[ChatMessage]
        model: str = "default"
    
    # Test model creation and validation
    request_data = {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ],
        "model": "test-model"
    }
    
    request = ChatRequest(**request_data)
    assert len(request.messages) == 2
    assert request.messages[0].role == "user"
    assert request.model == "test-model"
    
    # Test serialization
    json_data = request.model_dump()
    assert json_data['model'] == "test-model"
    assert len(json_data['messages']) == 2


def test_error_handling_patterns():
    """Test common error handling patterns we'll use in the API."""
    from fastapi import HTTPException
    
    # Test that HTTPException works
    try:
        raise HTTPException(status_code=404, detail="Model not found")
    except HTTPException as e:
        assert e.status_code == 404
        assert e.detail == "Model not found"
    
    # Test async error handling pattern
    async def mock_operation_that_fails():
        raise Exception("Operation failed")
    
    async def safe_operation():
        try:
            await mock_operation_that_fails()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    import asyncio
    result = asyncio.run(safe_operation())
    assert result["success"] is False
    assert "Operation failed" in result["error"]