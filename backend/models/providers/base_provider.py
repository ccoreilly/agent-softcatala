"""Base provider class for LLM providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain_core.language_models.chat_models import BaseChatModel


class BaseProvider(ABC):
    """Base class for all LLM providers."""
    
    def __init__(self, **kwargs):
        """Initialize the provider with configuration."""
        pass
    
    @abstractmethod
    def get_model(self, model_name: str, **kwargs) -> BaseChatModel:
        """Get a specific model instance."""
        pass
    
    @abstractmethod
    def list_models(self) -> List[str]:
        """List available models."""
        pass
    
    @abstractmethod
    def get_default_model(self) -> BaseChatModel:
        """Get the default model for this provider."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the provider."""
        pass