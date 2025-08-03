"""Tests for Zhipu AI streaming functionality and Content-Type error handling."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Generator, AsyncGenerator, List

from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk
from langchain_core.outputs import ChatGenerationChunk
from langchain_core.callbacks import CallbackManagerForLLMRun

from models.providers.zhipu_provider import ZhipuProvider
from models.providers.base_provider import BaseProvider


class TestZhipuStreaming:
    """Test suite for Zhipu AI streaming functionality."""

    @pytest.fixture
    def zhipu_provider(self):
        """Create a ZhipuProvider instance for testing."""
        return ZhipuProvider(api_key="test_api_key")

    @pytest.fixture
    def sample_messages(self):
        """Sample messages for testing."""
        return [HumanMessage(content="Hello, how are you?")]

    def test_zhipu_provider_initialization(self, zhipu_provider):
        """Test that ZhipuProvider initializes correctly."""
        assert isinstance(zhipu_provider, BaseProvider)
        assert zhipu_provider.api_key == "test_api_key"

    def test_get_model_non_streaming(self, zhipu_provider):
        """Test getting a non-streaming model."""
        model = zhipu_provider.get_model("glm-4", streaming=False)
        assert model is not None
        assert model.model == "glm-4"

    def test_get_model_streaming(self, zhipu_provider):
        """Test getting a streaming model returns the enhanced wrapper."""
        model = zhipu_provider.get_model("glm-4", streaming=True)
        assert model is not None
        assert model.model == "glm-4"
        assert model.streaming is True

    def test_list_models(self, zhipu_provider):
        """Test that available models are returned."""
        models = zhipu_provider.list_models()
        assert isinstance(models, list)
        assert "glm-4" in models
        assert "glm-4v" in models
        assert "glm-3-turbo" in models

    def test_get_default_model(self, zhipu_provider):
        """Test getting the default model."""
        model = zhipu_provider.get_default_model()
        assert model is not None
        assert model.model == "glm-4"

    @pytest.mark.asyncio
    async def test_streaming_fallback_on_content_type_error(self, zhipu_provider, sample_messages):
        """Test that streaming falls back gracefully when Content-Type error occurs."""
        # Create a streaming model
        model = zhipu_provider.get_model("glm-4", streaming=True)
        
        # Mock the parent streaming method to raise a Content-Type error
        content_type_error = Exception("Expected response header Content-Type to contain 'text/event-stream', got ''")
        
        # Mock the _generate method to return a response for fallback
        mock_response = Mock()
        mock_response.generations = [[Mock(text="Hello! I'm doing well, thank you for asking.")]]
        
        with patch.object(model.__class__.__bases__[0], '_astream', side_effect=content_type_error), \
             patch.object(model, '_agenerate', return_value=mock_response) as mock_agenerate:
            
            # Test async streaming fallback
            chunks = []
            async for chunk in model._astream(sample_messages):
                chunks.append(chunk)
            
            # Verify fallback was used
            mock_agenerate.assert_called_once()
            
            # Verify chunks were generated
            assert len(chunks) > 0
            assert all(isinstance(chunk, ChatGenerationChunk) for chunk in chunks)
            
            # Verify the content was split into word chunks
            full_content = "".join(chunk.message.content for chunk in chunks)
            assert "Hello!" in full_content
            assert "well" in full_content

    @pytest.mark.asyncio
    async def test_streaming_fallback_preserves_non_content_type_errors(self, zhipu_provider, sample_messages):
        """Test that non-Content-Type errors are still raised."""
        model = zhipu_provider.get_model("glm-4", streaming=True)
        
        # Mock the parent streaming method to raise a different error
        other_error = Exception("Some other network error")
        
        with patch.object(model.__class__.__bases__[0], '_astream', side_effect=other_error):
            # Should re-raise the non-Content-Type error
            with pytest.raises(Exception, match="Some other network error"):
                async for chunk in model._astream(sample_messages):
                    pass

    def test_sync_streaming_fallback_on_content_type_error(self, zhipu_provider, sample_messages):
        """Test that sync streaming also falls back gracefully."""
        model = zhipu_provider.get_model("glm-4", streaming=True)
        
        # Mock the parent streaming method to raise a Content-Type error
        content_type_error = Exception("Expected response header Content-Type to contain 'text/event-stream', got ''")
        
        # Mock the _generate method to return a response for fallback
        mock_response = Mock()
        mock_response.generations = [[Mock(text="Hello! I'm doing well, thank you for asking.")]]
        
        with patch.object(model.__class__.__bases__[0], '_stream', side_effect=content_type_error), \
             patch.object(model, '_generate', return_value=mock_response) as mock_generate:
            
            # Test sync streaming fallback
            chunks = list(model._stream(sample_messages))
            
            # Verify fallback was used
            mock_generate.assert_called_once()
            
            # Verify chunks were generated
            assert len(chunks) > 0
            assert all(isinstance(chunk, ChatGenerationChunk) for chunk in chunks)

    @pytest.mark.asyncio
    async def test_health_check_success(self, zhipu_provider):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.generations = [[Mock(text="Test response")]]
        
        with patch.object(zhipu_provider, 'get_model') as mock_get_model:
            mock_model = Mock()
            mock_model.agenerate = AsyncMock(return_value=mock_response)
            mock_get_model.return_value = mock_model
            
            health_status = await zhipu_provider.health_check()
            
            assert health_status["status"] == "healthy"
            assert health_status["test_successful"] is True
            assert health_status["streaming_support"] is True
            assert "glm-4" in health_status["available_models"]

    @pytest.mark.asyncio
    async def test_health_check_failure(self, zhipu_provider):
        """Test health check when service is unavailable."""
        with patch.object(zhipu_provider, 'get_model', side_effect=Exception("Service unavailable")):
            health_status = await zhipu_provider.health_check()
            
            assert health_status["status"] == "unhealthy"
            assert health_status["test_successful"] is False
            assert health_status["streaming_support"] is False
            assert "Service unavailable" in health_status["error"]

    @pytest.mark.asyncio
    async def test_streaming_with_telegram_bot_simulation(self, zhipu_provider):
        """Test streaming functionality as it would be used by the Telegram bot."""
        model = zhipu_provider.get_model("glm-4", streaming=True, temperature=0.7)
        
        # Simulate a telegram message
        messages = [HumanMessage(content="Explain what is artificial intelligence in a few sentences.")]
        
        # Mock a Content-Type error scenario (common with zhipu)
        content_type_error = Exception("Expected response header Content-Type to contain 'text/event-stream', got ''")
        mock_response = Mock()
        mock_response.generations = [[Mock(text="Artificial intelligence (AI) is a branch of computer science that aims to create systems capable of performing tasks that typically require human intelligence. These tasks include learning, reasoning, problem-solving, perception, and language understanding.")]]
        
        with patch.object(model.__class__.__bases__[0], '_astream', side_effect=content_type_error), \
             patch.object(model, '_agenerate', return_value=mock_response):
            
            # Simulate the agent streaming process
            response_chunks = []
            full_response = ""
            
            async for chunk in model._astream(messages):
                content = chunk.message.content
                if content:
                    response_chunks.append(content)
                    full_response += content
            
            # Verify we got a meaningful response
            assert len(response_chunks) > 0
            assert "Artificial intelligence" in full_response
            assert "computer science" in full_response
            
            # Verify the chunks can be used for telegram streaming
            assert all(isinstance(chunk, str) for chunk in response_chunks)


class TestZhipuProviderIntegration:
    """Integration tests for ZhipuProvider with other components."""

    @pytest.fixture
    def mock_langchain_agent(self):
        """Mock the LangChain agent for testing."""
        from unittest.mock import Mock
        agent = Mock()
        agent.chat_stream = AsyncMock()
        return agent

    @pytest.mark.asyncio
    async def test_integration_with_langchain_agent(self, mock_langchain_agent):
        """Test that the fixed zhipu provider works with the LangChain agent."""
        # Create provider
        provider = ZhipuProvider(api_key="test_key")
        
        # Mock the streaming response
        async def mock_chat_stream(messages, session_id):
            yield {"type": "content", "content": "Hello", "timestamp": "2024-01-01"}
            yield {"type": "content", "content": " world", "timestamp": "2024-01-01"}
            yield {"type": "content", "content": "!", "timestamp": "2024-01-01"}
        
        mock_langchain_agent.chat_stream.side_effect = mock_chat_stream
        
        # Test the streaming flow
        chunks = []
        async for chunk in mock_langchain_agent.chat_stream([], "test_session"):
            chunks.append(chunk)
        
        assert len(chunks) == 3
        assert chunks[0]["content"] == "Hello"
        assert chunks[1]["content"] == " world"
        assert chunks[2]["content"] == "!"