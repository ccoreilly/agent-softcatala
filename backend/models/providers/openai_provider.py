"""OpenAI provider implementation."""

import os
from typing import List, Dict, Any
import logging

from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI provider for OpenAI language models."""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (if not provided, will use OPENAI_KEY env var)
            base_url: Custom base URL for OpenAI API (optional)
        """
        self.api_key = api_key or os.getenv("OPENAI_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_KEY environment variable or pass api_key parameter.")
        
        self.base_url = base_url
        super().__init__()
    
    def get_model(self, model_name: str, **kwargs) -> BaseChatModel:
        """Get a specific OpenAI model instance.
        
        Args:
            model_name: Name of the model to load
            **kwargs: Additional parameters for the model
            
        Returns:
            ChatOpenAI instance
        """
        model_kwargs = {
            "model": model_name,
            "openai_api_key": self.api_key,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "top_p": kwargs.get("top_p", 1.0),
        }
        
        if self.base_url:
            model_kwargs["openai_api_base"] = self.base_url
        
        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in ["temperature", "max_tokens", "top_p"]:
                model_kwargs[key] = value
        
        return ChatOpenAI(**model_kwargs)
    
    def list_models(self) -> List[str]:
        """List available OpenAI models.
        
        Returns:
            List of model names
        """
        # Return commonly available OpenAI models
        # Note: OpenAI doesn't provide a public API endpoint to list all available models
        # so we return a curated list of common models
        return [
            "gpt-4.1-nano",
            "gpt-4.1-mini",
            "gpt-4o-mini",
        ]
    
    def get_default_model(self) -> BaseChatModel:
        """Get the default OpenAI model.
        
        Returns:
            ChatOpenAI instance with gpt-4.1-mini as default model
        """
        return self.get_model("gpt-4.1-mini")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI API health.
        
        Returns:
            Health status dictionary
        """
        try:
            # Try to create a model instance and make a simple call to verify connectivity
            model = self.get_model("gpt-4.1-mini")
            
            # Test with a minimal request
            test_response = await model.ainvoke("Hello")
            
            return {
                "status": "healthy",
                "provider": "openai",
                "default_model": "gpt-4.1-mini",
                "api_key_configured": bool(self.api_key),
                "base_url": self.base_url or "https://api.openai.com/v1",
                "available_models_count": len(self.list_models())
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "openai",
                "error": str(e),
                "api_key_configured": bool(self.api_key),
                "base_url": self.base_url or "https://api.openai.com/v1"
            }