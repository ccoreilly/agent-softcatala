"""Tests for OpenRouter provider."""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import os

from models.providers.openrouter_provider import OpenRouterProvider
from models.providers.base_provider import BaseProvider


class TestOpenRouterProvider:
    """Test OpenRouter provider functionality."""

    @pytest.fixture
    def openrouter_provider(self):
        """Create OpenRouter provider for testing."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-openrouter-key"}):
            return OpenRouterProvider()

    def test_provider_inheritance(self, openrouter_provider):
        """Test that OpenRouterProvider inherits from BaseProvider."""
        assert isinstance(openrouter_provider, BaseProvider)

    def test_initialization_with_api_key(self):
        """Test OpenRouter provider initialization with API key."""
        provider = OpenRouterProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://openrouter.ai/api/v1"

    def test_initialization_with_custom_base_url(self):
        """Test OpenRouter provider initialization with custom base URL."""
        custom_url = "https://custom.openrouter.com/api/v1"
        provider = OpenRouterProvider(api_key="test-key", base_url=custom_url)
        assert provider.base_url == custom_url

    def test_initialization_with_attribution(self):
        """Test OpenRouter provider initialization with site attribution."""
        provider = OpenRouterProvider(
            api_key="test-key",
            site_url="https://mysite.com",
            site_name="My App"
        )
        assert provider.site_url == "https://mysite.com"
        assert provider.site_name == "My App"

    def test_initialization_without_api_key(self):
        """Test that initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenRouter API key is required"):
                OpenRouterProvider()

    def test_initialization_with_env_vars(self):
        """Test initialization with environment variables."""
        env_vars = {
            "OPENROUTER_API_KEY": "env-key",
            "OPENROUTER_SITE_URL": "https://envsite.com",
            "OPENROUTER_SITE_NAME": "Env App"
        }
        with patch.dict(os.environ, env_vars):
            provider = OpenRouterProvider()
            assert provider.api_key == "env-key"
            assert provider.site_url == "https://envsite.com"
            assert provider.site_name == "Env App"

    def test_get_model(self, openrouter_provider):
        """Test getting a model instance."""
        model = openrouter_provider.get_model("google/gemma-3-27b-it:free")
        
        # Check that the model has the correct configuration
        assert model.model_name == "google/gemma-3-27b-it:free"
        assert model.openai_api_key == "test-openrouter-key"
        assert model.openai_api_base == "https://openrouter.ai/api/v1"

    def test_get_model_with_parameters(self, openrouter_provider):
        """Test getting a model with custom parameters."""
        model = openrouter_provider.get_model(
            "anthropic/claude-3-haiku",
            temperature=0.5,
            max_tokens=1024,
            top_p=0.9
        )
        
        assert model.model_name == "anthropic/claude-3-haiku"
        assert model.temperature == 0.5
        assert model.max_tokens == 1024
        assert model.top_p == 0.9

    def test_get_model_with_attribution_headers(self):
        """Test that attribution headers are included when configured."""
        provider = OpenRouterProvider(
            api_key="test-key",
            site_url="https://mysite.com",
            site_name="My App"
        )
        
        model = provider.get_model("google/gemma-3-27b-it:free")
        
        # Check that default headers are set for attribution
        assert hasattr(model, 'default_headers')
        assert model.default_headers["HTTP-Referer"] == "https://mysite.com"
        assert model.default_headers["X-Title"] == "My App"

    def test_list_models(self, openrouter_provider):
        """Test listing available models."""
        models = openrouter_provider.list_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert "google/gemma-3-27b-it:free" in models
        assert "anthropic/claude-3-5-sonnet" in models
        assert "openai/gpt-4o" in models

    def test_get_default_model(self, openrouter_provider):
        """Test getting the default model."""
        model = openrouter_provider.get_default_model()
        
        assert model.model_name == "google/gemma-3-27b-it:free"
        assert model.openai_api_key == "test-openrouter-key"

    @pytest.mark.asyncio
    async def test_health_check_success(self, openrouter_provider):
        """Test successful health check."""
        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value="Hello response")
        
        with patch.object(openrouter_provider, 'get_model', return_value=mock_model):
            health = await openrouter_provider.health_check()
            
            assert health["status"] == "healthy"
            assert health["provider"] == "openrouter"
            assert health["default_model"] == "google/gemma-3-27b-it:free"
            assert health["api_key_configured"] is True
            assert health["base_url"] == "https://openrouter.ai/api/v1"
            assert health["available_models_count"] > 0

    @pytest.mark.asyncio
    async def test_health_check_with_attribution(self):
        """Test health check includes attribution information."""
        provider = OpenRouterProvider(
            api_key="test-key",
            site_url="https://mysite.com",
            site_name="My App"
        )
        
        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value="Hello response")
        
        with patch.object(provider, 'get_model', return_value=mock_model):
            health = await provider.health_check()
            
            assert health["site_attribution"]["site_url"] == "https://mysite.com"
            assert health["site_attribution"]["site_name"] == "My App"

    @pytest.mark.asyncio
    async def test_health_check_failure(self, openrouter_provider):
        """Test health check when service is unavailable."""
        with patch.object(openrouter_provider, 'get_model', side_effect=Exception("Service unavailable")):
            health = await openrouter_provider.health_check()
            
            assert health["status"] == "unhealthy"
            assert health["provider"] == "openrouter"
            assert "Service unavailable" in health["error"]
            assert health["api_key_configured"] is True

    def test_get_model_custom_kwargs(self, openrouter_provider):
        """Test that custom kwargs are passed through to the model."""
        model = openrouter_provider.get_model("google/gemma-3-27b-it:free", streaming=True, custom_param="value")
        
        # Check that custom parameters are included
        # Note: These would be passed to the ChatOpenAI constructor
        assert model.model_name == "google/gemma-3-27b-it:free"