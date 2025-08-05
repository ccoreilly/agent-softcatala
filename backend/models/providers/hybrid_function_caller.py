"""Hybrid function calling wrapper that supports both native and fallback function calling."""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class HybridFunctionCaller:
    """Hybrid function calling implementation that supports both native and text-based function calling."""
    
    def __init__(self, provider, model, tools: List[BaseTool] = None):
        """Initialize the hybrid function caller.
        
        Args:
            provider: OpenRouter provider instance
            model: The language model instance
            tools: List of available tools
        """
        self.provider = provider
        self.model = model
        self.tools = tools or []
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        
        # Determine if the model supports native function calling
        model_name = getattr(model, 'model_name', getattr(model, 'model', 'unknown'))
        self.supports_native = provider.supports_native_function_calling(model_name)
        logger.info(f"Model {model_name} native function calling: {self.supports_native}")
    
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
            
        prompt = """At each turn, if you decide to invoke any of the function(s), it should be wrapped with ```tool_code```. The python methods described below are imported and available, you can only use defined methods. The generated code should be readable and efficient. The response to a method will be wrapped in ```tool_output``` use it to call more tools or generate a helpful, friendly response. When using a ```tool_call``` think step by step why and how it should be used.

The following Python methods are available:

"""
        
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
        
        # Add conversation history and current message
        conversation = ""
        for msg in messages:
            if isinstance(msg, HumanMessage):
                conversation += f"User: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                conversation += f"Assistant: {msg.content}\n"
        
        prompt += conversation
        return prompt
    
    async def call_with_tools(self, messages: List[BaseMessage]) -> BaseMessage:
        """Call the model with tools, using native or fallback approach."""
        if self.supports_native and self.tools:
            return await self._call_with_native_tools(messages)
        elif self.tools:
            return await self._call_with_fallback_tools(messages)
        else:
            # No tools available, regular call
            return await self.model.ainvoke(messages)
    
    async def _call_with_native_tools(self, messages: List[BaseMessage]) -> BaseMessage:
        """Handle native function calling."""
        try:
            # Bind tools to the model
            model_with_tools = self.model.bind_tools(self.tools)
            response = await model_with_tools.ainvoke(messages)
            
            # Check if response contains tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Execute tool calls
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    
                    if tool_name in self.tools_by_name:
                        try:
                            tool = self.tools_by_name[tool_name]
                            result = await tool.ainvoke(tool_args)
                            
                            # Create tool message
                            tool_message = ToolMessage(
                                content=str(result),
                                tool_call_id=tool_call['id']
                            )
                            
                            # Get final response with tool result
                            final_messages = messages + [response, tool_message]
                            final_response = await model_with_tools.ainvoke(final_messages)
                            return final_response
                            
                        except Exception as e:
                            logger.error(f"Error executing tool {tool_name}: {e}")
                            return AIMessage(content=f"Error executing tool {tool_name}: {str(e)}")
            
            return response
            
        except Exception as e:
            logger.warning(f"Native function calling failed: {e}, falling back to text-based approach")
            return await self._call_with_fallback_tools(messages)
    
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