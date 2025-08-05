"""OpenRouter provider implementation."""

import os
from typing import List, Dict, Any, Optional
import logging

from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.utils.utils import secret_from_env
from pydantic import Field, SecretStr

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class ChatOpenRouter(ChatOpenAI):
    """Custom ChatOpenAI subclass for OpenRouter with proper configuration."""
    
    openai_api_key: Optional[SecretStr] = Field(
        alias="api_key",
        default_factory=lambda: secret_from_env("OPENROUTER_API_KEY", default=None),
    )
    
    @property
    def lc_secrets(self) -> dict[str, str]:
        return {"openai_api_key": "OPENROUTER_API_KEY"}
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 model: str = "anthropic/claude-3-5-haiku",
                 **kwargs):
        """Initialize ChatOpenRouter with OpenRouter-specific defaults."""
        openai_api_key = (
            openai_api_key or os.environ.get("OPENROUTER_API_KEY")
        )
        
        if not openai_api_key:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable.")
        
        # Set OpenRouter-specific defaults
        kwargs.setdefault("base_url", "https://openrouter.ai/api/v1")
        kwargs.setdefault("temperature", 0.7)
        kwargs.setdefault("max_tokens", 2048)
        
        # Add OpenRouter-specific headers
        default_headers = kwargs.get("default_headers", {})
        
        # Add attribution headers if available
        site_url = os.getenv("OPENROUTER_SITE_URL")
        site_name = os.getenv("OPENROUTER_SITE_NAME")
        
        if site_url:
            default_headers["HTTP-Referer"] = site_url
        if site_name:
            default_headers["X-Title"] = site_name
            
        if default_headers:
            kwargs["default_headers"] = default_headers
        
        super().__init__(
            model=model,
            openai_api_key=openai_api_key,
            **kwargs
        )


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider for accessing multiple LLM models through OpenRouter API."""
    
    def __init__(self, api_key: str = None, base_url: str = None, site_url: str = None, site_name: str = None):
        """Initialize OpenRouter provider.
        
        Args:
            api_key: OpenRouter API key (if not provided, will use OPENROUTER_API_KEY env var)
            base_url: Custom base URL for OpenRouter API (defaults to https://openrouter.ai/api/v1)
            site_url: Your site URL for OpenRouter rankings (optional)
            site_name: Your site name for OpenRouter rankings (optional)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        self.site_url = site_url or os.getenv("OPENROUTER_SITE_URL")
        self.site_name = site_name or os.getenv("OPENROUTER_SITE_NAME")
        super().__init__()
    
    def get_model(self, model_name: str, **kwargs) -> BaseChatModel:
        """Get a specific OpenRouter model instance.
        
        Args:
            model_name: Name of the model to load (e.g., "anthropic/claude-3-5-haiku")
            **kwargs: Additional parameters for the model
            
        Returns:
            ChatOpenRouter instance configured for OpenRouter
        """
        model_kwargs = {
            "openai_api_key": self.api_key,
            "model": model_name,
            "base_url": self.base_url,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "top_p": kwargs.get("top_p", 1.0),
        }
        
        # Add OpenRouter-specific headers for attribution
        default_headers = {}
        if self.site_url:
            default_headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            default_headers["X-Title"] = self.site_name
        
        if default_headers:
            model_kwargs["default_headers"] = default_headers
        
        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in ["temperature", "max_tokens", "top_p"]:
                model_kwargs[key] = value
        
        return ChatOpenRouter(**model_kwargs)
    
    def list_models(self) -> List[str]:
        """List available OpenRouter models that support tool calling.
        
        Returns:
            List of tool-compatible model names
        """
        # Return a curated list of OpenRouter models that support tool calling
        # Based on https://openrouter.ai/models?supported_parameters=tools
        return [
            # Anthropic models (excellent tool support)
            "anthropic/claude-3-5-sonnet",
            "anthropic/claude-3-5-haiku", 
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-opus",
            
            # OpenAI models (excellent tool support)
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-4-turbo",
            "openai/gpt-4",
            "openai/gpt-3.5-turbo",
            
            # Google models (good tool support)
            "google/gemini-pro-1.5",
            "google/gemini-flash-1.5",
            "google/gemini-2.0-flash-exp",
            
            # Meta models (some tool support)
            "meta-llama/llama-3.1-405b-instruct",
            "meta-llama/llama-3.1-70b-instruct",
            "meta-llama/llama-3.1-8b-instruct",
            
            # Mistral models (good tool support)
            "mistralai/mistral-large",
            "mistralai/mixtral-8x7b-instruct",
            "mistralai/mixtral-8x22b-instruct",
            
            # Cohere models (good tool support)
            "cohere/command-r-plus",
            "cohere/command-r",
            
            # Free models that support tools
            "google/gemini-flash-1.5:free",
            "mistralai/mistral-7b-instruct:free",
        ]
    
    def get_default_model(self) -> BaseChatModel:
        """Get the default OpenRouter model that supports tool calling.
        
        Returns:
            ChatOpenRouter instance with anthropic/claude-3-5-haiku as default model
        """
        # Use Claude 3.5 Haiku as default - excellent tool support and cost-effective
        return self.get_model("anthropic/claude-3-5-haiku")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenRouter API health.
        
        Returns:
            Health status dictionary
        """
        try:
            # Try to create a model instance and make a simple call to verify connectivity
            model = self.get_model("anthropic/claude-3-5-haiku")
            
            # Test with a minimal request
            test_response = await model.ainvoke("Hello")
            
            return {
                "status": "healthy",
                "provider": "openrouter",
                "default_model": "anthropic/claude-3-5-haiku",
                "api_key_configured": bool(self.api_key),
                "base_url": self.base_url,
                "available_models_count": len(self.list_models()),
                "tool_calling_supported": True,
                "site_attribution": {
                    "site_url": self.site_url,
                    "site_name": self.site_name
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "openrouter",
                "error": str(e),
                "api_key_configured": bool(self.api_key),
                "base_url": self.base_url,
                "tool_calling_supported": False
            }