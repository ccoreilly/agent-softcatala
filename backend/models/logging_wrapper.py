"""Comprehensive logging wrapper for LLM interactions."""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)


class ComprehensiveLoggingHandler(AsyncCallbackHandler):
    """Comprehensive callback handler for logging all LLM interactions."""
    
    def __init__(self, session_id: str = None):
        """Initialize the logging handler.
        
        Args:
            session_id: Optional session identifier for tracking conversations
        """
        super().__init__()
        self.session_id = session_id or f"session_{int(time.time())}"
        self.conversation_log = []
        self.current_call_id = None
        
    def _format_message(self, message: BaseMessage) -> Dict[str, Any]:
        """Format a LangChain message for logging."""
        return {
            "type": message.__class__.__name__,
            "content": message.content,
            "timestamp": datetime.now().isoformat(),
            "additional_kwargs": getattr(message, 'additional_kwargs', {}),
            "tool_calls": getattr(message, 'tool_calls', None)
        }
    
    def _log_messages_chain(self, messages: List[BaseMessage], context: str = ""):
        """Log a complete message chain."""
        formatted_messages = [self._format_message(msg) for msg in messages]
        
        log_entry = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "message_count": len(messages),
            "messages": formatted_messages
        }
        
        logger.info(f"📋 MESSAGE CHAIN ({context}): {json.dumps(log_entry, indent=2, ensure_ascii=False)}")
        return log_entry
    
    async def on_llm_start(
        self, 
        serialized: Dict[str, Any], 
        prompts: List[str], 
        **kwargs: Any
    ) -> None:
        """Called when LLM starts processing."""
        self.current_call_id = f"call_{int(time.time() * 1000)}"
        
        log_entry = {
            "session_id": self.session_id,
            "call_id": self.current_call_id,
            "timestamp": datetime.now().isoformat(),
            "event": "llm_start",
            "model_info": serialized,
            "prompts": prompts,
            "kwargs": kwargs
        }
        
        logger.info(f"🚀 LLM CALL START: {json.dumps(log_entry, indent=2, ensure_ascii=False)}")
    
    async def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        **kwargs: Any,
    ) -> None:
        """Called when chat model starts processing."""
        self.current_call_id = f"call_{int(time.time() * 1000)}"
        
        # Log all message batches
        for i, message_batch in enumerate(messages):
            self._log_messages_chain(message_batch, f"chat_model_start_batch_{i}")
        
        log_entry = {
            "session_id": self.session_id,
            "call_id": self.current_call_id,
            "timestamp": datetime.now().isoformat(),
            "event": "chat_model_start",
            "model_info": serialized,
            "message_batches_count": len(messages),
            "total_messages": sum(len(batch) for batch in messages),
            "kwargs": kwargs
        }
        
        logger.info(f"💬 CHAT MODEL START: {json.dumps(log_entry, indent=2, ensure_ascii=False)}")
    
    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Called when LLM generates a new token."""
        # Only log tokens in debug mode to avoid spam
        if logger.isEnabledFor(logging.DEBUG):
            log_entry = {
                "session_id": self.session_id,
                "call_id": self.current_call_id,
                "timestamp": datetime.now().isoformat(),
                "event": "new_token",
                "token": token,
                "kwargs": kwargs
            }
            logger.debug(f"🔤 NEW TOKEN: {json.dumps(log_entry, ensure_ascii=False)}")
    
    async def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Called when LLM finishes processing."""
        log_entry = {
            "session_id": self.session_id,
            "call_id": self.current_call_id,
            "timestamp": datetime.now().isoformat(),
            "event": "llm_end",
            "response": str(response),
            "response_type": type(response).__name__,
            "kwargs": kwargs
        }
        
        logger.info(f"✅ LLM CALL END: {json.dumps(log_entry, indent=2, ensure_ascii=False)}")
    
    async def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        """Called when LLM encounters an error."""
        log_entry = {
            "session_id": self.session_id,
            "call_id": self.current_call_id,
            "timestamp": datetime.now().isoformat(),
            "event": "llm_error",
            "error": str(error),
            "error_type": type(error).__name__,
            "kwargs": kwargs
        }
        
        logger.error(f"❌ LLM ERROR: {json.dumps(log_entry, indent=2, ensure_ascii=False)}")
    
    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Called when tool starts executing."""
        log_entry = {
            "session_id": self.session_id,
            "call_id": self.current_call_id,
            "timestamp": datetime.now().isoformat(),
            "event": "tool_start",
            "tool_info": serialized,
            "input": input_str,
            "kwargs": kwargs
        }
        
        logger.info(f"🔧 TOOL START: {json.dumps(log_entry, indent=2, ensure_ascii=False)}")
    
    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when tool finishes executing."""
        log_entry = {
            "session_id": self.session_id,
            "call_id": self.current_call_id,
            "timestamp": datetime.now().isoformat(),
            "event": "tool_end",
            "output": output,
            "kwargs": kwargs
        }
        
        logger.info(f"✅ TOOL END: {json.dumps(log_entry, indent=2, ensure_ascii=False)}")
    
    async def on_tool_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        **kwargs: Any,
    ) -> None:
        """Called when tool encounters an error."""
        log_entry = {
            "session_id": self.session_id,
            "call_id": self.current_call_id,
            "timestamp": datetime.now().isoformat(),
            "event": "tool_error",
            "error": str(error),
            "error_type": type(error).__name__,
            "kwargs": kwargs
        }
        
        logger.error(f"❌ TOOL ERROR: {json.dumps(log_entry, indent=2, ensure_ascii=False)}")
    
    async def on_agent_action(self, action: Any, **kwargs: Any) -> None:
        """Called when agent takes an action."""
        log_entry = {
            "session_id": self.session_id,
            "call_id": self.current_call_id,
            "timestamp": datetime.now().isoformat(),
            "event": "agent_action",
            "action": {
                "tool": getattr(action, 'tool', 'unknown'),
                "tool_input": getattr(action, 'tool_input', {}),
                "log": getattr(action, 'log', '')
            },
            "kwargs": kwargs
        }
        
        logger.info(f"🎯 AGENT ACTION: {json.dumps(log_entry, indent=2, ensure_ascii=False)}")
    
    async def on_agent_finish(self, finish: Any, **kwargs: Any) -> None:
        """Called when agent finishes."""
        log_entry = {
            "session_id": self.session_id,
            "call_id": self.current_call_id,
            "timestamp": datetime.now().isoformat(),
            "event": "agent_finish",
            "finish": {
                "return_values": getattr(finish, 'return_values', {}),
                "log": getattr(finish, 'log', '')
            },
            "kwargs": kwargs
        }
        
        logger.info(f"🏁 AGENT FINISH: {json.dumps(log_entry, indent=2, ensure_ascii=False)}")


def add_logging_to_model(model: BaseChatModel, session_id: str = None) -> BaseChatModel:
    """Add comprehensive logging to a LangChain model without breaking compatibility.
    
    Since Pydantic models don't allow direct method patching, we'll just return
    the model with a session ID attached and rely on the callback handlers for logging.
    
    Args:
        model: The LLM model to add logging to
        session_id: Optional session identifier
        
    Returns:
        The original model with session tracking
    """
    session_id = session_id or f"session_{int(time.time())}"
    
    # For now, just add session tracking to the model
    # The actual logging will be handled by ComprehensiveLoggingHandler in callbacks
    try:
        model._logging_session_id = session_id
    except (AttributeError, ValueError):
        # Some models might not allow setting arbitrary attributes
        # In this case, we'll just return the model as-is
        pass
    
    return model


class LoggingModelWrapper:
    """A proper wrapper that inherits from the wrapped model to maintain Runnable compatibility."""
    
    def __new__(cls, model: BaseChatModel, session_id: str = None):
        """Create a new instance that properly inherits from the base model.
        
        Args:
            model: The LLM model to wrap
            session_id: Optional session identifier
            
        Returns:
            The original model with logging capabilities added
        """
        # Instead of creating a wrapper class, we'll just add logging to the original model
        # and return it directly to maintain full LangChain compatibility
        session_id = session_id or f"session_{int(time.time())}"
        
        # Add session tracking
        try:
            model._logging_session_id = session_id
        except (AttributeError, ValueError):
            # Some models might not allow setting arbitrary attributes
            pass
        
        # Add logging methods to the model instance
        _add_logging_methods_to_instance(model, session_id)
        
        return model


def _add_logging_methods_to_instance(model: BaseChatModel, session_id: str):
    """Add logging methods to a model instance without breaking LangChain compatibility."""
    logger = logging.getLogger(__name__)
    
    def _log_request(messages, **kwargs) -> str:
        """Log the request being sent to the LLM."""
        request_id = f"req_{int(time.time() * 1000)}"
        
        # Only log if we have actual messages
        if isinstance(messages, list) and len(messages) > 0:
            formatted_messages = []
            for msg in messages:
                if hasattr(msg, 'content'):
                    formatted_messages.append({
                        "type": msg.__class__.__name__,
                        "content": msg.content,
                        "additional_kwargs": getattr(msg, 'additional_kwargs', {}),
                        "tool_calls": getattr(msg, 'tool_calls', None)
                    })
            
            log_entry = {
                "session_id": session_id,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "model_info": {
                    "class": model.__class__.__name__,
                    "model_name": getattr(model, 'model_name', getattr(model, 'model', 'unknown')),
                    "temperature": getattr(model, 'temperature', None),
                    "max_tokens": getattr(model, 'max_tokens', None),
                },
                "messages": formatted_messages,
                "kwargs": kwargs
            }
            
            logger.info(f"📤 LLM REQUEST: {json.dumps(log_entry, indent=2, ensure_ascii=False)}")
        else:
            # For non-message inputs (like simple strings from chains)
            logger.info(f"📤 LLM SIMPLE REQUEST (Session: {session_id}): {messages}")
        
        return request_id
    
    def _log_response(request_id: str, response, duration_ms: float):
        """Log the response received from the LLM."""
        if hasattr(response, 'content'):
            response_data = {
                "content": response.content,
                "type": type(response).__name__,
                "additional_kwargs": getattr(response, 'additional_kwargs', {}),
                "tool_calls": getattr(response, 'tool_calls', None),
                "usage_metadata": getattr(response, 'usage_metadata', None)
            }
        else:
            response_data = {
                "content": str(response),
                "type": type(response).__name__
            }
        
        log_entry = {
            "session_id": session_id,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": duration_ms,
            "response": response_data
        }
        
        logger.info(f"📥 LLM RESPONSE: {json.dumps(log_entry, indent=2, ensure_ascii=False)}")
    
    def _log_error(request_id: str, error: Exception, duration_ms: float):
        """Log an error that occurred during LLM call."""
        log_entry = {
            "session_id": session_id,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": duration_ms,
            "error": str(error),
            "error_type": type(error).__name__
        }
        
        logger.error(f"❌ LLM ERROR: {json.dumps(log_entry, indent=2, ensure_ascii=False)}")
    
    # Store original methods to avoid infinite recursion
    if not hasattr(model, '_original_ainvoke'):
        model._original_ainvoke = model.ainvoke
    if not hasattr(model, '_original_invoke'):
        model._original_invoke = model.invoke
    
    # Create logged versions
    async def logged_ainvoke(input_data, config=None, **kwargs):
        """Async invoke with logging."""
        request_id = _log_request(input_data, **kwargs)
        start_time = time.time()
        
        try:
            response = await model._original_ainvoke(input_data, config=config, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            _log_response(request_id, response, duration_ms)
            return response
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            _log_error(request_id, e, duration_ms)
            raise
    
    def logged_invoke(input_data, config=None, **kwargs):
        """Sync invoke with logging."""
        request_id = _log_request(input_data, **kwargs)
        start_time = time.time()
        
        try:
            response = model._original_invoke(input_data, config=config, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            _log_response(request_id, response, duration_ms)
            return response
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            _log_error(request_id, e, duration_ms)
            raise
    
    # Only replace methods if not already replaced
    if not hasattr(model, '_logging_enabled'):
        try:
            # Use setattr to avoid Pydantic field validation issues
            object.__setattr__(model, 'ainvoke', logged_ainvoke)
            object.__setattr__(model, 'invoke', logged_invoke)
            object.__setattr__(model, '_logging_enabled', True)
            logger.info(f"✅ Added logging to {model.__class__.__name__} model")
        except Exception as e:
            logger.warning(f"⚠️ Could not add method logging to {model.__class__.__name__}: {e}")
            # If we can't override methods, that's okay - the callback handlers will still log


def create_comprehensive_config(session_id: str = None) -> RunnableConfig:
    """Create a runnable config with comprehensive logging."""
    logging_handler = ComprehensiveLoggingHandler(session_id)
    
    return RunnableConfig(
        callbacks=[logging_handler],
        tags=["comprehensive_logging"],
        metadata={"session_id": session_id or f"session_{int(time.time())}"}
    )
