"""OpenRouter provider implementation with fallback function calling."""

import os
import re
import json
from typing import List, Dict, Any, Optional
import logging

from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.utils.utils import secret_from_env
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
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
                 model: str = "google/gemma-3-27b-it:free",
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
    """OpenRouter provider for accessing multiple LLM models through OpenRouter API with fallback function calling."""
    
    # Models that support native function calling
    NATIVE_FUNCTION_CALLING_MODELS = {
        # # Anthropic models (excellent tool support)
        # "anthropic/claude-3-5-sonnet",
        # "anthropic/claude-3-5-haiku", 
        # "anthropic/claude-3-haiku",
        # "anthropic/claude-3-sonnet",
        # "anthropic/claude-3-opus",
        
        # # OpenAI models (excellent tool support)
        # "openai/gpt-4o",
        # "openai/gpt-4o-mini",
        # "openai/gpt-4-turbo",
        # "openai/gpt-4",
        # "openai/gpt-3.5-turbo",
        # "openai/gpt-oss-20b:free",
        
        # # Google models (good tool support)
        # "google/gemini-pro-1.5",
        # "google/gemini-flash-1.5",
        # "google/gemini-2.0-flash-exp",
        
        # # Meta models (some tool support)
        # "meta-llama/llama-3.1-405b-instruct",
        # "meta-llama/llama-3.1-70b-instruct",
        # "meta-llama/llama-3.1-8b-instruct",
        
        # # Mistral models (good tool support)
        # "mistralai/mistral-large",
        # "mistralai/mixtral-8x7b-instruct",
        # "mistralai/mixtral-8x22b-instruct",
        
        # # Cohere models (good tool support)
        # "cohere/command-r-plus",
        # "cohere/command-r",

        # Disponibles
        "openai/gpt-oss-20b:free",
        "deepseek/deepseek-chat-v3-0324:free",
        "google/gemini-2.0-flash-exp:free",
        "qwen/qwen3-235b-a22b:free",
        "qwen/qwen3-4b:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-small-3.1-24b-instruct:free",
        "mistralai/mistral-small-3.2-24b-instruct:free",
        "mistralai/mistral-7b-instruct:free"

    }
    
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
    
    def supports_native_function_calling(self, model_name: str) -> bool:
        """Check if a model supports native function calling."""
        return model_name in self.NATIVE_FUNCTION_CALLING_MODELS
    
    def extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract tool call from text response using regex (Philipp Schmid's approach)."""
        pattern = r"```tool_code\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            code = match.group(1).strip()
            try:
                # Try to parse as a function call
                # Expected format: function_name(arg1=value1, arg2=value2)
                func_pattern = r"(\w+)\((.*?)\)"
                func_match = re.search(func_pattern, code, re.DOTALL)
                if func_match:
                    func_name = func_match.group(1)
                    args_str = func_match.group(2)
                    
                    # Parse arguments
                    args = {}
                    if args_str.strip():
                        # Simple argument parsing for key=value pairs
                        arg_pairs = args_str.split(',')
                        for pair in arg_pairs:
                            if '=' in pair:
                                key, value = pair.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip('"\'')
                                args[key] = value
                    
                    return {
                        "name": func_name,
                        "arguments": args
                    }
            except Exception as e:
                logger.warning(f"Failed to parse tool call: {e}")
        return None
    
    def create_function_calling_prompt(self, tools: List[Dict], user_message: str) -> str:
        """Create a prompt for text-based function calling (Philipp Schmid's approach)."""
        prompt = """At each turn, if you decide to invoke any of the function(s), it should be wrapped with ```tool_code```. The python methods described below are imported and available, you can only use defined methods. The generated code should be readable and efficient. The response to a method will be wrapped in ```tool_output``` use it to call more tools or generate a helpful, friendly response. When using a ```tool_call``` think step by step why and how it should be used.

The following Python methods are available:

"""
        # Add function definitions
        for tool in tools:
            if hasattr(tool, 'definition'):
                definition = tool.definition
                name = definition.get('name', 'unknown')
                description = definition.get('description', 'No description available')
                parameters = definition.get('parameters', {}).get('properties', {})
                
                prompt += f"```python\ndef {name}("
                param_strs = []
                for param_name, param_info in parameters.items():
                    param_type = param_info.get('type', 'str')
                    param_strs.append(f"{param_name}: {param_type}")
                prompt += ", ".join(param_strs)
                prompt += f"):\n    \"\"\"{description}\n    \"\"\"\n```\n\n"
        
        prompt += f"User: {user_message}"
        return prompt
    
    def get_model(self, model_name: str, **kwargs) -> BaseChatModel:
        """Get a specific OpenRouter model instance.
        
        Args:
            model_name: Name of the model to load (e.g., "google/gemma-3-27b-it:free")
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
        """List available OpenRouter models with mixed function calling support.
        
        Returns:
            List of available model names (both native and fallback supported)
        """
        return [
            # # Free models (great for testing, may need fallback function calling)
            # "google/gemma-3-27b-it:free",
            # "google/gemini-flash-1.5:free",
            # "mistralai/mistral-7b-instruct:free",
            
            # # Anthropic models (native tool support)
            # "anthropic/claude-3-5-sonnet",
            # "anthropic/claude-3-5-haiku", 
            # "anthropic/claude-3-haiku",
            # "anthropic/claude-3-sonnet",
            # "anthropic/claude-3-opus",
            
            # # OpenAI models (native tool support)
            # "openai/gpt-4o",
            # "openai/gpt-4o-mini",
            # "openai/gpt-4-turbo",
            # "openai/gpt-4",
            # "openai/gpt-3.5-turbo",
            # "openai/gpt-oss-20b:free",
            
            # # Google models (mixed support)
            # "google/gemini-pro-1.5",
            # "google/gemini-flash-1.5",
            # "google/gemini-2.0-flash-exp",
            
            # # Meta models (fallback function calling)
            # "meta-llama/llama-3.1-405b-instruct",
            # "meta-llama/llama-3.1-70b-instruct",
            # "meta-llama/llama-3.1-8b-instruct",
            
            # # Mistral models (native tool support)
            # "mistralai/mistral-large",
            # "mistralai/mixtral-8x7b-instruct",
            # "mistralai/mixtral-8x22b-instruct",
            
            # # Cohere models (native tool support)
            # "cohere/command-r-plus",
            # "cohere/command-r",
            
            # # Other popular models (fallback function calling)
            # "qwen/qwen-2.5-72b-instruct",
            # "deepseek/deepseek-coder",
            # "perplexity/llama-3.1-sonar-large-128k-online",
            # "perplexity/llama-3.1-sonar-small-128k-online"
            
            # Disponibles
            "google/gemma-3-27b-it:free",
            "google/gemma-3n-e2b-it:free",
            "openai/gpt-oss-20b:free",
            "z-ai/glm-4.5-air:free",
            "moonshotai/kimi-k2:free",
            "deepseek/deepseek-chat-v3-0324:free",
            "deepseek/deepseek-r1-0528-qwen3-8b:free",
            "deepseek/deepseek-r1-0528:free",
            "google/gemini-2.0-flash-exp:free",
            "qwen/qwen3-4b:free",
            "qwen/qwen3-8b:free",
            "qwen/qwen3-14b:free",
            "qwen/qwen3-30b-a3b:free",
            "qwen/qwen3-235b-a22b:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "mistralai/mistral-small-3.1-24b-instruct:free",
            "mistralai/mistral-small-3.2-24b-instruct:free",
            "mistralai/mistral-7b-instruct:free"
        ]
    
    def get_default_model(self) -> BaseChatModel:
        """Get the default OpenRouter model.
        
        Returns:
            ChatOpenRouter instance with google/gemma-3-27b-it:free as default model
        """
        # Use Gemma 3 as default - free and supports fallback function calling
        return self.get_model("openai/gpt-oss-20b:free")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenRouter API health.
        
        Returns:
            Health status dictionary
        """
        try:
            # Try to create a model instance and make a simple call to verify connectivity
            model = self.get_model("google/gemma-3-27b-it:free")
            
            # Test with a minimal request
            test_response = await model.ainvoke("Hello")
            
            return {
                "status": "healthy",
                "provider": "openrouter",
                "default_model": "google/gemma-3-27b-it:free",
                "api_key_configured": bool(self.api_key),
                "base_url": self.base_url,
                "available_models_count": len(self.list_models()),
                "native_function_calling_models": len(self.NATIVE_FUNCTION_CALLING_MODELS),
                "fallback_function_calling_supported": True,
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
                "fallback_function_calling_supported": False
            }