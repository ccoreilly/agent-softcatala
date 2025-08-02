"""Zhipu AI provider implementation."""

import os
from typing import List, Dict, Any
import logging

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.language_models.chat_models import BaseChatModel

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class ZhipuProvider(BaseProvider):
    """Zhipu AI provider for GLM models."""
    
    def __init__(self, api_key: str):
        """Initialize Zhipu AI provider.
        
        Args:
            api_key: Zhipu AI API key
        """
        self.api_key = api_key
        os.environ["ZHIPUAI_API_KEY"] = api_key
        super().__init__()
    
    def get_model(self, model_name: str, **kwargs) -> BaseChatModel:
        """Get a specific Zhipu AI model instance.
        
        Args:
            model_name: Name of the model to load (e.g., "glm-4", "glm-3-turbo")
            **kwargs: Additional parameters for the model
            
        Returns:
            ChatZhipuAI instance
        """
        model_kwargs = {
            "model": model_name,
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 1.0),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        
        # Add streaming support if requested
        if kwargs.get("streaming", False):
            model_kwargs["streaming"] = True
        
        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in ["temperature", "top_p", "max_tokens", "streaming"]:
                model_kwargs[key] = value
        
        return ChatZhipuAI(**model_kwargs)
    
    def list_models(self) -> List[str]:
        """List available Zhipu AI models.
        
        Returns:
            List of model names
        """
        # Zhipu AI available models as of 2024
        return [
            "glm-4",
            "glm-4v",
            "glm-3-turbo"
        ]
    
    def get_default_model(self) -> BaseChatModel:
        """Get the default Zhipu AI model.
        
        Returns:
            ChatZhipuAI instance with GLM-4 model
        """
        return self.get_model("glm-4")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Zhipu AI service health.
        
        Returns:
            Health status dictionary
        """
        try:
            # Try to create a model instance
            model = self.get_model("glm-4")
            
            # Test with a simple message
            test_message = "Hello"
            response = await model.agenerate([[{"role": "user", "content": test_message}]])
            
            return {
                "status": "healthy",
                "available_models": self.list_models(),
                "test_successful": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "available_models": self.list_models(),
                "test_successful": False
            }