"""Model manager for handling multiple LLM providers."""

import os
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.language_models.chat_models import BaseChatModel

from .providers import OllamaProvider, ZhipuProvider

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported model providers."""
    OLLAMA = "ollama"
    ZHIPU = "zhipu"


class ModelManager:
    """Manages multiple LLM providers and models."""
    
    def __init__(self):
        self.providers = {}
        self.active_models = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers based on configuration."""
        # Initialize Ollama provider
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        try:
            self.providers[ModelProvider.OLLAMA] = OllamaProvider(ollama_url)
            logger.info(f"Initialized Ollama provider at {ollama_url}")
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama provider: {e}")
        
        # Initialize Zhipu AI provider
        zhipu_api_key = os.getenv("ZHIPUAI_API_KEY")
        if zhipu_api_key:
            try:
                self.providers[ModelProvider.ZHIPU] = ZhipuProvider(zhipu_api_key)
                logger.info("Initialized Zhipu AI provider")
            except Exception as e:
                logger.warning(f"Failed to initialize Zhipu AI provider: {e}")
        else:
            logger.warning("ZHIPUAI_API_KEY not found, Zhipu AI provider not initialized")
    
    def get_model(self, provider: str, model_name: str, **kwargs) -> BaseChatModel:
        """Get a specific model from a provider."""
        provider_enum = ModelProvider(provider.lower())
        
        if provider_enum not in self.providers:
            raise ValueError(f"Provider {provider} not available")
        
        return self.providers[provider_enum].get_model(model_name, **kwargs)
    
    def list_available_models(self) -> Dict[str, List[str]]:
        """List all available models from all providers."""
        models = {}
        for provider_name, provider in self.providers.items():
            try:
                models[provider_name.value] = provider.list_models()
            except Exception as e:
                logger.warning(f"Failed to list models for {provider_name}: {e}")
                models[provider_name.value] = []
        return models
    
    def get_default_model(self) -> BaseChatModel:
        """Get the default model based on availability."""
        # Try Ollama first
        if ModelProvider.OLLAMA in self.providers:
            try:
                return self.providers[ModelProvider.OLLAMA].get_default_model()
            except Exception as e:
                logger.warning(f"Failed to get default Ollama model: {e}")
        
        # Fall back to Zhipu AI
        if ModelProvider.ZHIPU in self.providers:
            try:
                return self.providers[ModelProvider.ZHIPU].get_default_model()
            except Exception as e:
                logger.warning(f"Failed to get default Zhipu model: {e}")
        
        raise RuntimeError("No available language models found")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of all providers."""
        health_status = {}
        for provider_name, provider in self.providers.items():
            try:
                health_status[provider_name.value] = await provider.health_check()
            except Exception as e:
                health_status[provider_name.value] = {
                    "status": "error",
                    "error": str(e)
                }
        return health_status