"""
Test our enhanced mocking system works correctly
"""
import pytest
from unittest.mock import patch


def test_langchain_imports_work():
    """Test that LangChain imports work with our mocking system."""
    # These should all work thanks to our module-level mocks
    from langchain import agents
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_core.tools import BaseTool
    from langchain_core.callbacks import AsyncCallbackHandler
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.runnables import RunnableConfig
    
    # They should all be mocks
    assert agents is not None
    assert HumanMessage is not None
    assert AIMessage is not None
    assert BaseTool is not None
    assert AsyncCallbackHandler is not None
    assert ChatPromptTemplate is not None
    assert MessagesPlaceholder is not None
    assert RunnableConfig is not None


def test_langchain_agent_import():
    """Test that we can import the LangChain agent."""
    from langchain_agent import LangChainAgent
    
    # Create an instance - should work with mocked dependencies
    agent = LangChainAgent()
    assert agent is not None
    assert hasattr(agent, 'current_model')


@pytest.mark.asyncio
async def test_mocked_agent_functionality(mock_langchain_agent):
    """Test that our mocked agent works as expected."""
    # Test health check
    health = await mock_langchain_agent.check_health()
    assert health['status'] == 'healthy'
    
    # Test model listing
    models = await mock_langchain_agent.get_available_models()
    assert isinstance(models, list)
    assert len(models) > 0
    
    # Test model switching
    result = mock_langchain_agent.switch_model('test-model')
    assert result is True
    assert mock_langchain_agent.current_model == 'test-model'


@pytest.mark.asyncio
async def test_mocked_chat_streaming(mock_langchain_agent):
    """Test that chat streaming works with our mock."""
    messages = [{"role": "user", "content": "Hello"}]
    
    chunks = []
    async for chunk in mock_langchain_agent.chat_stream(messages):
        chunks.append(chunk)
    
    # Should get multiple chunks forming "Hello world!"
    assert len(chunks) > 0
    assert all('content' in chunk for chunk in chunks)


def test_mock_fastapi_app(mock_fastapi_app):
    """Test that our mocked FastAPI app works."""
    assert mock_fastapi_app is not None
    assert hasattr(mock_fastapi_app, 'routes')
    assert len(mock_fastapi_app.routes) > 0


def test_tools_import():
    """Test that tools can be imported."""
    from tools.web_browser import WebBrowserTool
    
    # Should be mocked but importable
    tool = WebBrowserTool()
    assert tool is not None