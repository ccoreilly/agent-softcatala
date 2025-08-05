"""OpenRouter provider implementation."""

import os
from typing import List, Dict, Any
import logging

from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


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
            model_name: Name of the model to load (e.g., "anthropic/claude-3-sonnet")
            **kwargs: Additional parameters for the model
            
        Returns:
            ChatOpenAI instance configured for OpenRouter
        """
        model_kwargs = {
            "model": model_name,
            "openai_api_key": self.api_key,
            "openai_api_base": self.base_url,
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
        
        return ChatOpenAI(**model_kwargs)
    
    def list_models(self) -> List[str]:
        """List available OpenRouter models.
        
        Returns:
            List of popular model names
        """
        # Return a curated list of popular OpenRouter models
        # In a production environment, you might want to fetch this from OpenRouter's API
        return [
            "anthropic/claude-3-5-sonnet",
            "anthropic/claude-3-haiku",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            "google/gemini-pro",
            "google/gemini-pro-1.5",
            "meta-llama/llama-3.1-405b-instruct",
            "meta-llama/llama-3.1-70b-instruct",
            "meta-llama/llama-3.1-8b-instruct",
            "mistralai/mistral-7b-instruct",
            "mistralai/mixtral-8x7b-instruct",
            "mistralai/mixtral-8x22b-instruct",
            "qwen/qwen-2.5-72b-instruct",
            "deepseek/deepseek-coder",
            "perplexity/llama-3.1-sonar-large-128k-online",
            "perplexity/llama-3.1-sonar-small-128k-online"
        ]
    
    def get_default_model(self) -> BaseChatModel:
        """Get the default OpenRouter model.
        
        Returns:
            ChatOpenAI instance with anthropic/claude-3-5-sonnet as default model
        """
        return self.get_model("anthropic/claude-3-5-sonnet")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenRouter API health.
        
        Returns:
            Health status dictionary
        """
        try:
            # Try to create a model instance and make a simple call to verify connectivity
            model = self.get_model("openai/gpt-4o-mini")
            
            # Test with a minimal request
            test_response = await model.ainvoke("Hello")
            
            return {
                "status": "healthy",
                "provider": "openrouter",
                "default_model": "anthropic/claude-3-5-sonnet",
                "api_key_configured": bool(self.api_key),
                "base_url": self.base_url,
                "available_models_count": len(self.list_models()),
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
                "base_url": self.base_url
            }