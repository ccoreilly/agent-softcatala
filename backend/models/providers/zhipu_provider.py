"""Zhipu AI provider implementation."""

import os
from typing import List, Dict, Any
import logging

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.messages import BaseMessage

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
        
        # Handle streaming with improved error handling
        streaming = kwargs.get("streaming", False)
        if streaming:
            # Create a wrapper class to handle streaming issues
            class StreamingZhipuAI(ChatZhipuAI):
                def _stream(self, messages: List[BaseMessage], stop: List[str] = None, 
                           run_manager: CallbackManagerForLLMRun = None, **kwargs) -> Any:
                    """Override streaming to handle zhipu-specific issues."""
                    try:
                        # Try normal streaming first
                        return super()._stream(messages, stop, run_manager, **kwargs)
                    except Exception as e:
                        # Check if it's a Content-Type related error
                        error_str = str(e)
                        if "Content-Type" in error_str and "text/event-stream" in error_str:
                            logger.warning(f"Zhipu streaming failed with Content-Type error: {e}")
                            logger.info("Falling back to non-streaming mode for this request")
                            
                            # Fall back to non-streaming mode and simulate streaming
                            result = self._generate(messages, stop, run_manager, **kwargs)
                            
                            # Simulate streaming by yielding the entire response as chunks
                            if result and result.generations:
                                full_text = result.generations[0][0].text
                                # Split the response into word-like chunks for better UX
                                words = full_text.split()
                                accumulated = ""
                                for i, word in enumerate(words):
                                    accumulated += word
                                    if i < len(words) - 1:
                                        accumulated += " "
                                    
                                    # Create a streaming chunk-like response
                                    from langchain_core.outputs import ChatGenerationChunk
                                    from langchain_core.messages import AIMessageChunk
                                    
                                    chunk = ChatGenerationChunk(
                                        message=AIMessageChunk(content=word + (" " if i < len(words) - 1 else "")),
                                        generation_info={}
                                    )
                                    yield chunk
                            return
                        else:
                            # Re-raise non-Content-Type related errors
                            raise e
                            
                async def _astream(self, messages: List[BaseMessage], stop: List[str] = None,
                                 run_manager: CallbackManagerForLLMRun = None, **kwargs) -> Any:
                    """Override async streaming to handle zhipu-specific issues."""
                    try:
                        # Try normal async streaming first
                        async for chunk in super()._astream(messages, stop, run_manager, **kwargs):
                            yield chunk
                    except Exception as e:
                        # Check if it's a Content-Type related error
                        error_str = str(e)
                        if "Content-Type" in error_str and "text/event-stream" in error_str:
                            logger.warning(f"Zhipu async streaming failed with Content-Type error: {e}")
                            logger.info("Falling back to non-streaming mode for this request")
                            
                            # Fall back to non-streaming mode and simulate streaming
                            result = await self._agenerate(messages, stop, run_manager, **kwargs)
                            
                            # Simulate streaming by yielding the entire response as chunks
                            if result and result.generations:
                                full_text = result.generations[0][0].text
                                # Split the response into word-like chunks for better UX
                                words = full_text.split()
                                
                                for i, word in enumerate(words):
                                    # Create a streaming chunk-like response
                                    from langchain_core.outputs import ChatGenerationChunk
                                    from langchain_core.messages import AIMessageChunk
                                    
                                    chunk = ChatGenerationChunk(
                                        message=AIMessageChunk(content=word + (" " if i < len(words) - 1 else "")),
                                        generation_info={}
                                    )
                                    yield chunk
                            return
                        else:
                            # Re-raise non-Content-Type related errors
                            raise e
            
            model_kwargs["streaming"] = True
            return StreamingZhipuAI(**model_kwargs)
        
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
            
            # Test with a simple message - use non-streaming for health check
            from langchain_core.messages import HumanMessage
            test_message = [HumanMessage(content="Hello")]
            response = await model.agenerate([test_message])
            
            return {
                "status": "healthy",
                "available_models": self.list_models(),
                "test_successful": True,
                "streaming_support": True  # We now have fallback support
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "available_models": self.list_models(),
                "test_successful": False,
                "streaming_support": False
            }