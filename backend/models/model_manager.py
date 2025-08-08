"""Model manager for handling multiple LLM providers."""

import os
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.language_models.chat_models import BaseChatModel

from .providers import OllamaProvider, ZhipuProvider, OpenAIProvider, OpenRouterProvider

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported model providers."""
    OLLAMA = "ollama"
    ZHIPU = "zhipu"
    OPENAI = "openai"
    OPENROUTER = "openrouter"


class ModelManager:
    """Manages multiple LLM providers and models."""
    
    def __init__(self):
        self.providers = {}
        self.active_models = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers based on configuration."""
        # Initialize Ollama provider
        ollama_url = os.getenv("OLLAMA_URL")
        if ollama_url and ollama_url.strip():
            try:
                self.providers[ModelProvider.OLLAMA] = OllamaProvider(ollama_url)
                logger.info(f"Initialized Ollama provider at {ollama_url}")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama provider: {e}")
        else:
            logger.warning("OLLAMA_URL not found or empty, Ollama provider not initialized")
        
        # Initialize Zhipu AI provider
        zhipu_api_key = os.getenv("ZHIPUAI_API_KEY")
        if zhipu_api_key:
            try:
                # Support Z.AI endpoint override
                zhipu_base_url = os.getenv("ZHIPUAI_BASE_URL")
                if zhipu_base_url:
                    self.providers[ModelProvider.ZHIPU] = ZhipuProvider(zhipu_api_key, zhipu_base_url)
                    logger.info(f"Initialized Zhipu AI provider with custom endpoint: {zhipu_base_url}")
                else:
                    self.providers[ModelProvider.ZHIPU] = ZhipuProvider(zhipu_api_key)
                    logger.info("Initialized Zhipu AI provider with default endpoint")
            except Exception as e:
                logger.warning(f"Failed to initialize Zhipu AI provider: {e}")
        else:
            logger.warning("ZHIPUAI_API_KEY not found, Zhipu AI provider not initialized")
        
        # Initialize OpenAI provider
        openai_api_key = os.getenv("OPENAI_KEY")
        if openai_api_key:
            try:
                # Support custom OpenAI base URL if needed
                openai_base_url = os.getenv("OPENAI_BASE_URL")
                if openai_base_url:
                    self.providers[ModelProvider.OPENAI] = OpenAIProvider(openai_api_key, openai_base_url)
                    logger.info(f"Initialized OpenAI provider with custom endpoint: {openai_base_url}")
                else:
                    self.providers[ModelProvider.OPENAI] = OpenAIProvider(openai_api_key)
                    logger.info("Initialized OpenAI provider with default endpoint")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e}")
        else:
            logger.warning("OPENAI_KEY not found, OpenAI provider not initialized")
        
        # Initialize OpenRouter provider
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_api_key:
            try:
                # Support custom OpenRouter base URL, site URL and site name if needed
                openrouter_base_url = os.getenv("OPENROUTER_BASE_URL")
                openrouter_site_url = os.getenv("OPENROUTER_SITE_URL")
                openrouter_site_name = os.getenv("OPENROUTER_SITE_NAME")
                
                self.providers[ModelProvider.OPENROUTER] = OpenRouterProvider(
                    openrouter_api_key, 
                    openrouter_base_url, 
                    openrouter_site_url, 
                    openrouter_site_name
                )
                logger.info(f"Initialized OpenRouter provider with endpoint: {openrouter_base_url or 'https://openrouter.ai/api/v1'}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenRouter provider: {e}")
        else:
            logger.warning("OPENROUTER_API_KEY not found, OpenRouter provider not initialized")
    
    def get_model(self, provider: str, model_name: str, **kwargs) -> BaseChatModel:
        """Get a specific model from a provider."""
        provider_enum = ModelProvider(provider.lower())
        
        if provider_enum not in self.providers:
            raise ValueError(f"Provider {provider} not available")
        
        return self.providers[provider_enum].get_model(model_name, **kwargs)
    
    def get_provider(self, provider: str) -> BaseChatModel:
        """Get a specific provider."""
        provider_enum = ModelProvider(provider.lower())
        if provider_enum not in self.providers:
            raise ValueError(f"Provider {provider} not available")
        return self.providers[provider_enum]
    
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
        
        # Fall back to OpenRouter (free model)
        if ModelProvider.OPENROUTER in self.providers:
            try:
                return self.providers[ModelProvider.OPENROUTER].get_default_model()
            except Exception as e:
                logger.warning(f"Failed to get default OpenRouter model: {e}")
        
        # Fall back to OpenAI
        if ModelProvider.OPENAI in self.providers:
            try:
                return self.providers[ModelProvider.OPENAI].get_default_model()
            except Exception as e:
                logger.warning(f"Failed to get default OpenAI model: {e}")
        
        # Fall back to Zhipu AI
        if ModelProvider.ZHIPU in self.providers:
            try:
                return self.providers[ModelProvider.ZHIPU].get_default_model()
            except Exception as e:
                logger.warning(f"Failed to get default Zhipu model: {e}")
        
        raise RuntimeError("No available language models found")
    
    def get_provider_for_default_model(self):
        """Get the provider instance for the default model."""
        # Try Ollama first
        if ModelProvider.OLLAMA in self.providers:
            try:
                # Just check if it can provide a model
                self.providers[ModelProvider.OLLAMA].get_default_model()
                return self.providers[ModelProvider.OLLAMA]
            except Exception as e:
                logger.warning(f"Failed to get default Ollama model: {e}")
        
        # Fall back to OpenRouter (free model)
        if ModelProvider.OPENROUTER in self.providers:
            try:
                # Just check if it can provide a model
                self.providers[ModelProvider.OPENROUTER].get_default_model()
                return self.providers[ModelProvider.OPENROUTER]
            except Exception as e:
                logger.warning(f"Failed to get default OpenRouter model: {e}")
        
        # Fall back to OpenAI
        if ModelProvider.OPENAI in self.providers:
            try:
                # Just check if it can provide a model
                self.providers[ModelProvider.OPENAI].get_default_model()
                return self.providers[ModelProvider.OPENAI]
            except Exception as e:
                logger.warning(f"Failed to get default OpenAI model: {e}")
        
        # Fall back to Zhipu
        if ModelProvider.ZHIPU in self.providers:
            try:
                # Just check if it can provide a model
                self.providers[ModelProvider.ZHIPU].get_default_model()
                return self.providers[ModelProvider.ZHIPU]
            except Exception as e:
                logger.warning(f"Failed to get default Zhipu model: {e}")
        
        raise ValueError("No providers available for default model")
    
    def get_required_env_vars(self) -> List[str]:
        """Get list of environment variables that could configure providers."""
        return [
            "OLLAMA_URL (for Ollama provider)",
            "ZHIPUAI_API_KEY (for Zhipu AI provider)", 
            "OPENAI_KEY (for OpenAI provider)",
            "OPENROUTER_API_KEY (for OpenRouter provider)"
        ]
    
    def get_configured_provider_names(self) -> List[str]:
        """Get list of successfully configured provider names."""
        return [provider_enum.value.title() for provider_enum in self.providers.keys()]
    
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