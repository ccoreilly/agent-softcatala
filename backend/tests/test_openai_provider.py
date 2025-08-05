"""Tests for OpenAI provider implementation."""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from models.providers.openai_provider import OpenAIProvider
from models.providers.base_provider import BaseProvider


class TestOpenAIProvider:
    """Test suite for OpenAI provider functionality."""

    @pytest.fixture
    def openai_provider(self):
        """Create an OpenAIProvider instance for testing."""
        return OpenAIProvider(api_key="test_api_key")

    @pytest.fixture
    def sample_messages(self):
        """Sample messages for testing."""
        return [HumanMessage(content="Hello, how are you?")]

    def test_openai_provider_initialization(self, openai_provider):
        """Test that OpenAIProvider initializes correctly."""
        assert isinstance(openai_provider, BaseProvider)
        assert openai_provider.api_key == "test_api_key"
        assert openai_provider.base_url is None

    def test_openai_provider_initialization_with_base_url(self):
        """Test that OpenAIProvider initializes correctly with custom base URL."""
        provider = OpenAIProvider(api_key="test_api_key", base_url="https://custom.openai.com/v1")
        assert provider.api_key == "test_api_key"
        assert provider.base_url == "https://custom.openai.com/v1"

    @patch.dict(os.environ, {'OPENAI_KEY': 'env_api_key'})
    def test_openai_provider_initialization_from_env(self):
        """Test that OpenAIProvider initializes from environment variable."""
        provider = OpenAIProvider()
        assert provider.api_key == "env_api_key"

    def test_openai_provider_initialization_no_api_key(self):
        """Test that OpenAIProvider raises error when no API key is provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                OpenAIProvider()

    def test_get_model(self, openai_provider):
        """Test getting an OpenAI model."""
        model = openai_provider.get_model("gpt-4.1-mini")
        assert isinstance(model, ChatOpenAI)
        assert model.model_name == "gpt-4.1-mini"
        assert model.openai_api_key.get_secret_value() == "test_api_key"

    def test_get_model_with_parameters(self, openai_provider):
        """Test getting an OpenAI model with custom parameters."""
        model = openai_provider.get_model(
            "gpt-4o", 
            temperature=0.5, 
            max_tokens=1000,
            top_p=0.9
        )
        assert isinstance(model, ChatOpenAI)
        assert model.model_name == "gpt-4o"
        assert model.temperature == 0.5
        assert model.max_tokens == 1000
        assert model.top_p == 0.9

    def test_get_model_with_base_url(self):
        """Test getting an OpenAI model with custom base URL."""
        provider = OpenAIProvider(api_key="test_key", base_url="https://custom.openai.com/v1")
        model = provider.get_model("gpt-4.1-mini")
        assert isinstance(model, ChatOpenAI)
        assert model.openai_api_base == "https://custom.openai.com/v1"

    def test_list_models(self, openai_provider):
        """Test that available models are returned."""
        models = openai_provider.list_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "gpt-4.1-mini" in models
        assert "gpt-4o" in models
        assert "gpt-3.5-turbo" in models

    def test_get_default_model(self, openai_provider):
        """Test getting the default model."""
        model = openai_provider.get_default_model()
        assert isinstance(model, ChatOpenAI)
        assert model.model_name == "gpt-4.1-mini"

    @pytest.mark.asyncio
    async def test_health_check_success(self, openai_provider):
        """Test successful health check."""
        # Mock the model's ainvoke method
        with patch.object(openai_provider, 'get_model') as mock_get_model:
            mock_model = AsyncMock()
            mock_model.ainvoke.return_value = AIMessage(content="Hello!")
            mock_get_model.return_value = mock_model
            
            health = await openai_provider.health_check()
            
            assert health["status"] == "healthy"
            assert health["provider"] == "openai"
            assert health["default_model"] == "gpt-4.1-mini"
            assert health["api_key_configured"] is True
            assert health["base_url"] == "https://api.openai.com/v1"
            assert health["available_models_count"] > 0

    @pytest.mark.asyncio
    async def test_health_check_failure(self, openai_provider):
        """Test health check failure."""
        # Mock the model's ainvoke method to raise an exception
        with patch.object(openai_provider, 'get_model') as mock_get_model:
            mock_model = AsyncMock()
            mock_model.ainvoke.side_effect = Exception("API error")
            mock_get_model.return_value = mock_model
            
            health = await openai_provider.health_check()
            
            assert health["status"] == "unhealthy"
            assert health["provider"] == "openai"
            assert "error" in health
            assert health["api_key_configured"] is True
            assert health["base_url"] == "https://api.openai.com/v1"

    @pytest.mark.asyncio
    async def test_health_check_with_custom_base_url(self):
        """Test health check with custom base URL."""
        provider = OpenAIProvider(api_key="test_key", base_url="https://custom.openai.com/v1")
        
        with patch.object(provider, 'get_model') as mock_get_model:
            mock_model = AsyncMock()
            mock_model.ainvoke.return_value = AIMessage(content="Hello!")
            mock_get_model.return_value = mock_model
            
            health = await provider.health_check()
            
            assert health["status"] == "healthy"
            assert health["base_url"] == "https://custom.openai.com/v1"


class TestOpenAIProviderIntegration:
    """Integration tests for OpenAIProvider with other components."""
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_KEY"),
        reason="OPENAI_KEY environment variable not set"
    )
    @pytest.mark.asyncio
    async def test_real_openai_api_call(self):
        """Test real OpenAI API call (only when API key is available)."""
        provider = OpenAIProvider()
        model = provider.get_model("gpt-4.1-mini", temperature=0.1, max_tokens=50)
        
        # Make a simple API call
        response = await model.ainvoke([HumanMessage(content="Say 'Hello, World!' and nothing else.")])
        
        assert isinstance(response, AIMessage)
        assert len(response.content) > 0
        assert "Hello" in response.content

    @pytest.mark.skipif(
        not os.getenv("OPENAI_KEY"),
        reason="OPENAI_KEY environment variable not set"
    )
    @pytest.mark.asyncio
    async def test_real_health_check(self):
        """Test real health check (only when API key is available)."""
        provider = OpenAIProvider()
        health = await provider.health_check()
        
        assert health["status"] == "healthy"
        assert health["provider"] == "openai"
        assert health["api_key_configured"] is True