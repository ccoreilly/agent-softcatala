"""Ollama provider implementation."""

import httpx
from typing import List, Dict, Any
import logging

from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Ollama provider for local LLM models."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize Ollama provider.
        
        Args:
            base_url: The base URL for the Ollama service
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        super().__init__()
    
    def get_model(self, model_name: str, **kwargs) -> BaseChatModel:
        """Get a specific Ollama model instance.
        
        Args:
            model_name: Name of the model to load
            **kwargs: Additional parameters for the model
            
        Returns:
            ChatOllama instance
        """
        model_kwargs = {
            "model": model_name,
            "base_url": self.base_url,
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 1.0),
            "num_predict": kwargs.get("max_tokens", 2048),
        }
        
        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in ["temperature", "top_p", "max_tokens"]:
                model_kwargs[key] = value
        
        return ChatOllama(**model_kwargs)
    
    def list_models(self) -> List[str]:
        """List available models in Ollama.
        
        Returns:
            List of model names
        """
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    def get_default_model(self) -> BaseChatModel:
        """Get the default Ollama model.
        
        Returns:
            ChatOllama instance with default model
        """
        models = self.list_models()
        if not models:
            # Try common models if listing fails
            default_models = ["llama3.2", "llama3.1", "llama2", "mistral"]
            for model in default_models:
                try:
                    return self.get_model(model)
                except Exception:
                    continue
            raise RuntimeError("No Ollama models available")
        
        # Use the first available model
        return self.get_model(models[0])
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama service health.
        
        Returns:
            Health status dictionary
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            
            return {
                "status": "healthy",
                "base_url": self.base_url,
                "models_count": len(data.get("models", [])),
                "available_models": [model["name"] for model in data.get("models", [])]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "base_url": self.base_url,
                "error": str(e)
            }