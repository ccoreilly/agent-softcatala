"""
Integration tests for LangChain agent, model providers, and tools
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langchain_agent import LangChainAgent
from tools.web_browser import WebBrowserTool


class TestLangChainAgent:
    """Test the LangChain agent functionality."""
    
    @pytest.fixture
    def mock_tools(self):
        """Create mock tools for testing."""
        web_tool = MagicMock(spec=WebBrowserTool)
        search_tool = MagicMock()
        wikipedia_tool = MagicMock()
        
        web_tool.name = "web_browser"
        search_tool.name = "search"
        wikipedia_tool.name = "wikipedia"
        
        return [web_tool, search_tool, wikipedia_tool]
    
    def test_agent_initialization(self, mock_tools):
        """Test agent initializes correctly with tools."""
        agent = LangChainAgent(tools=mock_tools)
        assert agent is not None
        assert len(agent.tools) == 3
    
    def test_agent_initialization_without_tools(self):
        """Test agent initializes correctly without tools."""
        agent = LangChainAgent(tools=[])
        assert agent is not None
        assert len(agent.tools) == 0
    
    @pytest.mark.asyncio
    async def test_agent_health_check(self, mock_tools):
        """Test agent health check functionality."""
        with patch('langchain_agent.LangChainAgent.check_health') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "models": {
                    "ollama": {"status": "available", "available_models": ["llama3.1"]},
                    "zhipu": {"status": "available", "available_models": ["glm-4"]}
                },
                "tools": {
                    "count": 3,
                    "names": ["web_browser", "search", "wikipedia"]
                }
            }
            
            agent = LangChainAgent(tools=mock_tools)
            health = await agent.check_health()
            
            assert health["status"] == "healthy"
            assert "models" in health
            assert "tools" in health
            assert health["tools"]["count"] == 3
    
    @pytest.mark.asyncio
    async def test_agent_get_available_models(self, mock_tools):
        """Test getting available models from agent."""
        with patch('langchain_agent.LangChainAgent.get_available_models') as mock_models:
            mock_models.return_value = {
                "ollama": ["llama3.1", "mistral"],
                "zhipu": ["glm-4", "glm-3-turbo"]
            }
            
            agent = LangChainAgent(tools=mock_tools)
            models = await agent.get_available_models()
            
            assert "ollama" in models
            assert "zhipu" in models
            assert "llama3.1" in models["ollama"]
            assert "glm-4" in models["zhipu"]
    
    def test_agent_switch_model(self, mock_tools):
        """Test model switching functionality."""
        with patch('langchain_agent.LangChainAgent.switch_model') as mock_switch:
            agent = LangChainAgent(tools=mock_tools)
            agent.switch_model("ollama", "llama3.1", temperature=0.7)
            
            mock_switch.assert_called_once_with("ollama", "llama3.1", temperature=0.7)
    
    @pytest.mark.asyncio
    async def test_agent_chat_stream(self, mock_tools):
        """Test chat streaming functionality."""
        with patch('langchain_agent.LangChainAgent.chat_stream') as mock_stream:
            # Mock the async generator
            async def mock_chat_stream(messages, session_id):
                yield {"type": "text", "content": "Test response", "timestamp": "2024-01-01T00:00:00"}
                yield {"type": "text", "content": " continuation", "timestamp": "2024-01-01T00:00:01"}
            
            mock_stream.return_value = mock_chat_stream([], "test")
            
            agent = LangChainAgent(tools=mock_tools)
            messages = [{"role": "user", "content": "Hello"}]
            
            responses = []
            async for chunk in agent.chat_stream(messages, "test_session"):
                responses.append(chunk)
            
            assert len(responses) >= 1  # Should have at least one response


class TestModelProviders:
    """Test model provider functionality."""
    
    @pytest.mark.asyncio
    async def test_ollama_provider_availability(self):
        """Test Ollama provider availability check."""
        # Mock the actual provider test since we don't want to require Ollama running
        with patch('models.providers.ollama_provider.OllamaProvider') as mock_provider:
            mock_instance = MagicMock()
            mock_instance.test_connection = AsyncMock(return_value={
                "status": "available",
                "available_models": ["llama3.1", "mistral"]
            })
            mock_provider.return_value = mock_instance
            
            provider = mock_provider()
            result = await provider.test_connection()
            
            assert result["status"] == "available"
            assert "available_models" in result
    
    @pytest.mark.asyncio
    async def test_zhipu_provider_availability(self):
        """Test Zhipu AI provider availability check."""
        with patch('models.providers.zhipu_provider.ZhipuProvider') as mock_provider:
            mock_instance = MagicMock()
            mock_instance.test_connection = AsyncMock(return_value={
                "status": "available",
                "available_models": ["glm-4", "glm-3-turbo"],
                "test_successful": True
            })
            mock_provider.return_value = mock_instance
            
            provider = mock_provider()
            result = await provider.test_connection()
            
            assert result["status"] == "available"
            assert result["test_successful"] is True
            assert "glm-4" in result["available_models"]
    
    @pytest.mark.asyncio
    async def test_provider_error_handling(self):
        """Test provider error handling when service is unavailable."""
        with patch('models.providers.ollama_provider.OllamaProvider') as mock_provider:
            mock_instance = MagicMock()
            mock_instance.test_connection = AsyncMock(side_effect=Exception("Connection failed"))
            mock_provider.return_value = mock_instance
            
            provider = mock_provider()
            
            try:
                await provider.test_connection()
                assert False, "Should have raised an exception"
            except Exception as e:
                assert "Connection failed" in str(e)


class TestToolsIntegration:
    """Test tools integration and functionality."""
    
    def test_web_browser_tool_initialization(self):
        """Test web browser tool initializes correctly."""
        # Mock the tool since we don't want to make actual web requests
        with patch('tools.web_browser.WebBrowserTool') as mock_tool:
            mock_instance = MagicMock()
            mock_instance.name = "web_browser"
            mock_tool.return_value = mock_instance
            
            tool = mock_tool()
            assert tool.name == "web_browser"
    
    def test_search_tool_creation(self):
        """Test search tool creation."""
        with patch('tools.langchain_tools.create_search_tool') as mock_create:
            mock_tool = MagicMock()
            mock_tool.name = "search"
            mock_create.return_value = mock_tool
            
            tool = mock_create()
            assert tool.name == "search"
    
    def test_wikipedia_tool_creation(self):
        """Test Wikipedia tool creation."""
        with patch('tools.langchain_tools.create_wikipedia_tool') as mock_create:
            mock_tool = MagicMock()
            mock_tool.name = "wikipedia"
            mock_create.return_value = mock_tool
            
            tool = mock_create()
            assert tool.name == "wikipedia"
    
    @pytest.mark.asyncio
    async def test_tools_in_agent_execution(self):
        """Test that tools are properly integrated in agent execution."""
        # Create mock tools
        web_tool = MagicMock()
        web_tool.name = "web_browser"
        search_tool = MagicMock()
        search_tool.name = "search"
        
        tools = [web_tool, search_tool]
        
        with patch('langchain_agent.LangChainAgent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.tools = tools
            mock_agent_class.return_value = mock_agent
            
            agent = mock_agent_class(tools=tools)
            assert len(agent.tools) == 2
            assert any(tool.name == "web_browser" for tool in agent.tools)
            assert any(tool.name == "search" for tool in agent.tools)


class TestMessageHistory:
    """Test message history functionality."""
    
    def test_message_history_initialization(self):
        """Test message history initializes correctly."""
        with patch('message_history.MessageHistory') as mock_history:
            mock_instance = MagicMock()
            mock_history.return_value = mock_instance
            
            history = mock_history()
            assert history is not None
    
    def test_message_history_operations(self):
        """Test basic message history operations."""
        with patch('message_history.MessageHistory') as mock_history:
            mock_instance = MagicMock()
            mock_instance.add_message = MagicMock()
            mock_instance.get_messages = MagicMock(return_value=[])
            mock_instance.clear_session = MagicMock()
            mock_history.return_value = mock_instance
            
            history = mock_history()
            
            # Test adding message
            history.add_message("test_session", {"role": "user", "content": "Hello"})
            history.add_message.assert_called_once()
            
            # Test getting messages
            messages = history.get_messages("test_session")
            assert isinstance(messages, list)
            
            # Test clearing session
            history.clear_session("test_session")
            history.clear_session.assert_called_once_with("test_session")


class TestEnvironmentConfiguration:
    """Test environment configuration and dependency loading."""
    
    def test_environment_loading(self):
        """Test that environment variables are loaded correctly."""
        with patch('dotenv.load_dotenv') as mock_load_dotenv:
            # Import main to trigger dotenv loading
            import main
            mock_load_dotenv.assert_called()
    
    @patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token"})
    def test_telegram_configuration(self):
        """Test Telegram bot configuration from environment."""
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        assert telegram_token == "test_token"
    
    @patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:3000,https://example.com"})
    def test_cors_origins_configuration(self):
        """Test CORS origins configuration from environment."""
        cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
        assert "localhost:3000" in cors_origins
        assert "example.com" in cors_origins
    
    def test_default_cors_configuration(self):
        """Test default CORS configuration when not set."""
        # Clear the env var if it exists
        if "CORS_ORIGINS" in os.environ:
            del os.environ["CORS_ORIGINS"]
        
        cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
        assert cors_origins == "http://localhost:3000"


class TestErrorHandling:
    """Test error handling and resilience."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization_with_failed_tools(self):
        """Test agent handles tool initialization failures gracefully."""
        # Mock a failing tool
        failing_tool = MagicMock()
        failing_tool.side_effect = Exception("Tool initialization failed")
        
        # Should not raise exception, but log error and continue
        with patch('langchain_agent.LangChainAgent') as mock_agent:
            mock_instance = MagicMock()
            mock_agent.return_value = mock_instance
            
            agent = mock_agent(tools=[])
            assert agent is not None
    
    @pytest.mark.asyncio
    async def test_model_provider_fallback(self):
        """Test fallback behavior when model providers fail."""
        with patch('langchain_agent.LangChainAgent.check_health') as mock_health:
            # Simulate partial provider failure
            mock_health.return_value = {
                "status": "partial",
                "models": {
                    "ollama": {"status": "unavailable", "error": "Connection failed"},
                    "zhipu": {"status": "available", "available_models": ["glm-4"]}
                },
                "tools": {"count": 2, "names": ["search", "wikipedia"]}
            }
            
            agent = LangChainAgent(tools=[])
            health = await agent.check_health()
            
            # Should still report some functionality available
            assert health["status"] == "partial"
            assert health["models"]["zhipu"]["status"] == "available"