import httpx
import json
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
from datetime import datetime

from tools.base import BaseTool

# Setup logging for debugging
logger = logging.getLogger(__name__)


class Agent:
    """Main agent class that handles LLM interaction and tool execution"""
    
    def __init__(self, ollama_url: str, model: str, tools: List[BaseTool]):
        self.ollama_url = ollama_url.rstrip('/')
        self.model = model
        self.tools = {tool.definition.name: tool for tool in tools}
        self.client = httpx.AsyncClient(timeout=120.0)
    
    def _build_ollama_tools(self) -> List[Dict[str, Any]]:
        """Convert tools to Ollama's expected format"""
        ollama_tools = []
        
        for tool_name, tool in self.tools.items():
            tool_def = tool.definition
            
            # Convert tool parameters to JSON schema format
            properties = {}
            required = []
            
            for param in tool_def.parameters:
                properties[param.name] = {
                    "type": param.type,
                    "description": param.description
                }
                if param.required:
                    required.append(param.name)
            
            ollama_tool = {
                "type": "function",
                "function": {
                    "name": tool_def.name,
                    "description": tool_def.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }
            ollama_tools.append(ollama_tool)
        
        return ollama_tools
    
    async def check_health(self) -> bool:
        """Check if the Ollama service is healthy"""
        try:
            response = await self.client.get(f"{self.ollama_url}/api/tags")
            response.raise_for_status()
            return True
        except Exception:
            raise Exception("Ollama service is not accessible")
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama"""
        try:
            response = await self.client.get(f"{self.ollama_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            raise Exception(f"Failed to get models: {str(e)}")
    
    async def chat_stream(self, messages: List[Dict], session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat responses with tool execution"""
        # Convert messages to Ollama format
        ollama_messages = []
        
        for msg in messages:
            ollama_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        try:
            # Build request payload
            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": True
            }
            
            # Add tools if available
            ollama_tools = self._build_ollama_tools()
            if ollama_tools:
                payload["tools"] = ollama_tools
            
            # Log the request for debugging
            logger.info(f"Making Ollama request to {self.ollama_url}/api/chat")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            # Make request to Ollama
            async with self.client.stream(
                "POST",
                f"{self.ollama_url}/api/chat",
                json=payload
            ) as response:
                logger.debug(f"Ollama response status: {response.status_code}")
                logger.debug(f"Ollama response headers: {dict(response.headers)}")
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            
                            # Handle content streaming
                            if "message" in chunk and "content" in chunk["message"]:
                                content = chunk["message"]["content"]
                                if content:  # Only yield non-empty content
                                    yield {
                                        "type": "content",
                                        "content": content,
                                        "timestamp": datetime.now().isoformat()
                                    }
                            
                            # Handle tool calls
                            if "message" in chunk and "tool_calls" in chunk["message"]:
                                tool_calls = chunk["message"]["tool_calls"]
                                if tool_calls:
                                    for tool_call in tool_calls:
                                        if "function" in tool_call:
                                            function_data = tool_call["function"]
                                            tool_name = function_data.get("name")
                                            arguments = function_data.get("arguments", {})
                                            
                                            if tool_name in self.tools:
                                                # Notify about tool call
                                                yield {
                                                    "type": "tool_call",
                                                    "tool": tool_name,
                                                    "parameters": arguments,
                                                    "timestamp": datetime.now().isoformat()
                                                }
                                                
                                                # Execute the tool
                                                try:
                                                    logger.info(f"Executing tool: {tool_name} with parameters: {arguments}")
                                                    result = await self._execute_tool(tool_name, arguments)
                                                    logger.info(f"Tool {tool_name} completed successfully")
                                                    yield {
                                                        "type": "tool_result",
                                                        "tool": tool_name,
                                                        "result": result,
                                                        "timestamp": datetime.now().isoformat()
                                                    }
                                                    
                                                    # Continue conversation with tool result
                                                    # Add the assistant's tool call message
                                                    ollama_messages.append({
                                                        "role": "assistant",
                                                        "content": "",
                                                        "tool_calls": tool_calls
                                                    })
                                                    
                                                    # Add tool result as tool message
                                                    ollama_messages.append({
                                                        "role": "tool",
                                                        "content": json.dumps(result)
                                                    })
                                                    
                                                    # Get follow-up response
                                                    follow_up_payload = {
                                                        "model": self.model,
                                                        "messages": ollama_messages,
                                                        "stream": True
                                                    }
                                                    
                                                    if ollama_tools:
                                                        follow_up_payload["tools"] = ollama_tools
                                                    
                                                    logger.debug(f"Making follow-up request after tool execution")
                                                    logger.debug(f"Follow-up payload: {json.dumps(follow_up_payload, indent=2)}")
                                                    
                                                    async with self.client.stream(
                                                        "POST",
                                                        f"{self.ollama_url}/api/chat",
                                                        json=follow_up_payload
                                                    ) as follow_response:
                                                        logger.debug(f"Follow-up response status: {follow_response.status_code}")
                                                        follow_response.raise_for_status()
                                                        
                                                        async for follow_line in follow_response.aiter_lines():
                                                            if follow_line.strip():
                                                                try:
                                                                    follow_chunk = json.loads(follow_line)
                                                                    if "message" in follow_chunk and "content" in follow_chunk["message"]:
                                                                        follow_content = follow_chunk["message"]["content"]
                                                                        if follow_content:
                                                                            yield {
                                                                                "type": "content",
                                                                                "content": follow_content,
                                                                                "timestamp": datetime.now().isoformat()
                                                                            }
                                                                        
                                                                        if follow_chunk.get("done", False):
                                                                            return
                                                                except json.JSONDecodeError:
                                                                    continue
                                                
                                                except Exception as e:
                                                    logger.error(f"Tool {tool_name} failed: {str(e)}", exc_info=True)
                                                    yield {
                                                        "type": "tool_error",
                                                        "tool": tool_name,
                                                        "error": str(e),
                                                        "timestamp": datetime.now().isoformat()
                                                    }
                            
                            # Check if response is done
                            if chunk.get("done", False):
                                return
                                
                        except json.JSONDecodeError:
                            continue
                
        except Exception as e:
            logger.error(f"Error in chat_stream: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        return await tool.execute(**parameters)