"""Hybrid function calling wrapper that supports both native and fallback function calling."""

import re
import json
import logging
import time
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class HybridFunctionCaller:
    """Fallback function calling implementation for models that don't support native function calling."""
    
    def __init__(self, provider, model, tools: List[BaseTool] = None, use_catalan: bool = False):
        """Initialize the fallback function caller.
        
        Args:
            provider: OpenRouter provider instance
            model: The language model instance
            tools: List of available tools
            use_catalan: Whether to use Catalan language for fallback prompts
        """
        self.provider = provider
        self.model = model
        self.tools = tools or []
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.use_catalan = use_catalan
        
        logger.info(f"Fallback function caller initialized with {len(self.tools)} tools")
        logger.info(f"Using Catalan fallback prompts: {self.use_catalan}")
    
    def _extract_tool_call_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract tool call from text response using regex pattern."""
        pattern = r"```tool_code\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            code = match.group(1).strip()
            try:
                # Parse function call: function_name(arg1=value1, arg2=value2)
                func_pattern = r"(\w+)\((.*?)\)"
                func_match = re.search(func_pattern, code, re.DOTALL)
                if func_match:
                    func_name = func_match.group(1)
                    args_str = func_match.group(2)
                    
                    # Parse arguments
                    args = {}
                    if args_str.strip():
                        # Handle different argument formats
                        # Try to parse as key=value pairs
                        arg_pairs = args_str.split(',')
                        for pair in arg_pairs:
                            if '=' in pair:
                                key, value = pair.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip('"\'')
                                # Try to convert to appropriate type
                                try:
                                    # Try float first, then int, then keep as string
                                    if '.' in value:
                                        args[key] = float(value)
                                    elif value.isdigit():
                                        args[key] = int(value)
                                    else:
                                        args[key] = value
                                except ValueError:
                                    args[key] = value
                    
                    return {
                        "name": func_name,
                        "arguments": args
                    }
            except Exception as e:
                logger.warning(f"Failed to parse tool call: {e}")
        return None
    
    def _create_fallback_prompt(self, messages: List[BaseMessage]) -> str:
        """Create a prompt for text-based function calling."""
        if not self.tools:
            return messages[-1].content if messages else ""
        
        if self.use_catalan:
            return self._create_catalan_fallback_prompt(messages)
        else:
            return self._create_english_fallback_prompt(messages)
    
    def _create_english_fallback_prompt(self, messages: List[BaseMessage]) -> str:
        """Create an English prompt for text-based function calling."""
        prompt = """At each turn, if you decide to invoke any of the function(s), it should be wrapped with ```tool_code```. The python methods described below are imported and available, you can only use defined methods. The generated code should be readable and efficient. The response to a method will be wrapped in ```tool_output``` use it to call more tools or generate a helpful, friendly response. When using a ```tool_call``` think step by step why and how it should be used.

The following Python methods are available:

"""
        return self._build_prompt_with_tools(prompt, messages, "User", "Assistant")
    
    def _create_catalan_fallback_prompt(self, messages: List[BaseMessage]) -> str:
        """Create a Catalan prompt for text-based function calling."""
        prompt = """En cada torn, si decideixes invocar qualsevol de les funcions, ha d'estar embolcallada amb ```tool_code```. Els mètodes python descrits a continuació estan importats i disponibles, només pots utilitzar mètodes definits. El codi generat ha de ser llegible i eficient. La resposta a un mètode s'embolcallarà amb ```tool_output``` utilitzeu-lo per cridar més eines o generar una resposta útil i amigable. Quan utilitzis un ```tool_call``` pensa pas a pas per què i com s'ha d'utilitzar.

Els següents mètodes Python estan disponibles:

"""
        return self._build_prompt_with_tools(prompt, messages, "Usuari", "Assistent")
    
    def _build_prompt_with_tools(self, base_prompt: str, messages: List[BaseMessage], user_label: str, assistant_label: str) -> str:
        """Build the complete prompt with tool definitions and conversation history."""
        # Extract system messages and combine with function calling instructions
        system_content = ""
        conversation_messages = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_content += msg.content + "\n\n"
            else:
                conversation_messages.append(msg)
        
        # Start with system content if available
        if system_content:
            prompt = system_content.strip() + "\n\n" + base_prompt
        else:
            prompt = base_prompt
        
        # Add function definitions
        for tool in self.tools:
            name = tool.name
            description = tool.description
            
            # Get parameters from tool schema
            if hasattr(tool, 'args_schema') and tool.args_schema:
                schema = tool.args_schema.schema()
                properties = schema.get('properties', {})
                
                prompt += f"```python\ndef {name}("
                param_strs = []
                for param_name, param_info in properties.items():
                    param_type = param_info.get('type', 'str')
                    # Map JSON schema types to Python types
                    type_mapping = {
                        'string': 'str',
                        'integer': 'int', 
                        'number': 'float',
                        'boolean': 'bool',
                        'array': 'list',
                        'object': 'dict'
                    }
                    python_type = type_mapping.get(param_type, 'str')
                    param_strs.append(f"{param_name}: {python_type}")
                
                prompt += ", ".join(param_strs)
                prompt += f"):\n    \"\"\"{description}\n"
                
                # Add parameter descriptions
                for param_name, param_info in properties.items():
                    param_desc = param_info.get('description', '')
                    if param_desc:
                        prompt += f"    {param_name}: {param_desc}\n"
                
                prompt += '    """\n```\n\n'
            else:
                prompt += f"```python\ndef {name}():\n    \"\"\"{description}\"\"\"\n```\n\n"
        
        # Add conversation history (excluding system messages)
        conversation = ""
        for msg in conversation_messages:
            if isinstance(msg, HumanMessage):
                conversation += f"{user_label}: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                conversation += f"{assistant_label}: {msg.content}\n"
        
        prompt += conversation
        return prompt
    
    def _log_messages_chain(self, messages: List[BaseMessage], context: str = ""):
        """Log the complete message chain."""
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "type": msg.__class__.__name__,
                "content": msg.content,
                "timestamp": datetime.now().isoformat(),
                "additional_kwargs": getattr(msg, 'additional_kwargs', {}),
                "tool_calls": getattr(msg, 'tool_calls', None)
            })
        
        log_entry = {
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "message_count": len(messages),
            "messages": formatted_messages,
            "use_catalan": self.use_catalan,
            "tools_available": [tool.name for tool in self.tools]
        }
        
        logger.info(f"📋 FALLBACK CALLER MESSAGE CHAIN ({context}): {json.dumps(log_entry, indent=2, ensure_ascii=False)}")
    
    async def call_with_tools(self, messages: List[BaseMessage]) -> BaseMessage:
        """Call the model with tools using fallback function calling approach."""
        start_time = time.time()
        call_id = f"fallback_call_{int(time.time() * 1000)}"
        
        # Log the input message chain
        self._log_messages_chain(messages, f"call_input_{call_id}")
        
        logger.info(f"🔄 FALLBACK FUNCTION CALLER START (ID: {call_id}):")
        logger.info(f"  🔧 Tools available: {len(self.tools)}")
        logger.info(f"  📝 Tool names: {[tool.name for tool in self.tools]}")
        logger.info(f"  🌍 Language: {'Catalan' if self.use_catalan else 'English'}")
        
        try:
            if self.tools:
                logger.info(f"  🔄 Using FALLBACK function calling for {call_id}")
                result = await self._call_with_fallback_tools(messages)
            else:
                logger.info(f"  💬 Using REGULAR call (no tools) for {call_id}")
                result = await self.model.ainvoke(messages)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the result
            result_log = {
                "call_id": call_id,
                "timestamp": datetime.now().isoformat(),
                "duration_ms": duration_ms,
                "result_type": type(result).__name__,
                "result_content": result.content if hasattr(result, 'content') else str(result),
                "language": "catalan" if self.use_catalan else "english"
            }
            
            logger.info(f"✅ FALLBACK FUNCTION CALLER SUCCESS ({call_id}): {json.dumps(result_log, indent=2, ensure_ascii=False)}")
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            error_log = {
                "call_id": call_id,
                "timestamp": datetime.now().isoformat(),
                "duration_ms": duration_ms,
                "error": str(e),
                "error_type": type(e).__name__,
                "language": "catalan" if self.use_catalan else "english"
            }
            
            logger.error(f"❌ FALLBACK FUNCTION CALLER ERROR ({call_id}): {json.dumps(error_log, indent=2, ensure_ascii=False)}")
            raise
    

    
    async def _call_with_fallback_tools(self, messages: List[BaseMessage]) -> BaseMessage:
        """Handle text-based function calling fallback."""
        # Create the special prompt for function calling
        prompt = self._create_fallback_prompt(messages)
        
        # Get response from model
        response = await self.model.ainvoke([HumanMessage(content=prompt)])
        
        if not isinstance(response, AIMessage):
            return response
            
        # Check if response contains a tool call
        tool_call = self._extract_tool_call_from_text(response.content)
        
        if tool_call:
            tool_name = tool_call['name']
            tool_args = tool_call['arguments']
            
            if tool_name in self.tools_by_name:
                try:
                    tool = self.tools_by_name[tool_name]
                    result = await tool.ainvoke(tool_args)
                    
                    # Create tool output format
                    tool_output = f"```tool_output\n{result}\n```"
                    
                    # Get final response with tool result
                    final_prompt = prompt + "\n" + response.content + "\n" + tool_output
                    final_response = await self.model.ainvoke([HumanMessage(content=final_prompt)])
                    
                    return final_response
                    
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    return AIMessage(content=f"Error executing tool {tool_name}: {str(e)}")
            else:
                logger.warning(f"Tool {tool_name} not found in available tools")
                return AIMessage(content=f"Tool {tool_name} is not available.")
        
        return response