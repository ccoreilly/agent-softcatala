"""Zhipu AI / Z.AI provider implementation."""

import os
from typing import List, Dict, Any
import logging

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.messages import BaseMessage, HumanMessage

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class ZhipuProvider(BaseProvider):
    """Zhipu AI / Z.AI provider for GLM models."""
    
    def __init__(self, api_key: str, base_url: str = None):
        """Initialize Zhipu AI / Z.AI provider.
        
        Args:
            api_key: Zhipu AI / Z.AI API key
            base_url: Override base URL for Z.AI endpoint (defaults to Zhipu if not specified)
        """
        super().__init__()
        self.api_key = api_key
        # Use Z.AI/Zhipu endpoint - both Z.AI and Zhipu use the same API endpoint
        # Z.AI is the new brand for Zhipu AI but uses the same API infrastructure
        self.base_url = base_url or "https://open.bigmodel.cn/api/paas/v4/"
        
        # Set environment variables for langchain compatibility
        os.environ["ZHIPUAI_API_KEY"] = api_key
        if self.base_url:
            os.environ["ZHIPUAI_BASE_URL"] = self.base_url
        
    def get_model(self, model_name: str, **kwargs) -> BaseChatModel:
        """Get a specific model instance."""
        model_kwargs = {
            "model": model_name,
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 1.0),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        
        # Add base_url if configured
        if self.base_url:
            model_kwargs["base_url"] = self.base_url
            
        # Add additional kwargs
        for key, value in kwargs.items():
            if key not in ["temperature", "top_p", "max_tokens"]:
                model_kwargs[key] = value
        
        try:
            return ChatZhipuAI(**model_kwargs)
        except Exception as e:
            logger.error(f"Failed to create Z.AI/Zhipu model {model_name}: {e}")
            raise
        
    def list_models(self) -> List[str]:
        """List available GLM models including Z.AI models."""
        return [
            "glm-4.5-flash",  # New Z.AI default model - fast and efficient
            "glm-4.5-air",    # Z.AI lightweight model
            "glm-4.5",        # Z.AI flagship model
            "glm-4-9b",       # Previous generation
            "glm-4",
            "glm-4-0520",
            "glm-4-plus",
            "glm-4-flash",
            "glm-4-air",
            "glm-4-airx",
            "glm-4v-plus",
            "glm-3-turbo"
        ]
        
    def get_default_model(self) -> BaseChatModel:
        """Get the default model - now GLM-4.5-flash for Z.AI."""
        return self.get_model("glm-4.5-flash")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Z.AI/Zhipu AI service health."""
        try:
            # Try to create a model instance with the default model
            model = self.get_model("glm-4.5-flash")
            
            # Test with a simple message
            test_message = [HumanMessage(content="Hello")]
            response = await model.agenerate([test_message])
            
            return {
                "status": "healthy",
                "provider": "Z.AI/Zhipu",
                "available_models": self.list_models(),
                "test_successful": True,
                "endpoint": self.base_url,
                "default_model": "glm-4.5-flash"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "Z.AI/Zhipu", 
                "error": str(e),
                "available_models": self.list_models(),
                "test_successful": False,
                "endpoint": self.base_url,
                "default_model": "glm-4.5-flash"
            }