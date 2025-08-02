import httpx
import json
import re
from typing import List, Dict, Any, AsyncGenerator, Optional
from datetime import datetime

from tools.base import BaseTool


class Agent:
    """Main agent class that handles LLM interaction and tool execution"""
    
    def __init__(self, ollama_url: str, model: str, tools: List[BaseTool]):
        self.ollama_url = ollama_url.rstrip('/')
        self.model = model
        self.tools = {tool.definition.name: tool for tool in tools}
        self.client = httpx.AsyncClient(timeout=120.0)
        
        # System prompt that includes tool descriptions
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt including available tools"""
        base_prompt = """You are a helpful AI assistant with access to tools. You can help users with various tasks and answer questions.

When you need to use a tool, format your tool call as follows:
TOOL_CALL: tool_name
PARAMETERS: {"param1": "value1", "param2": "value2"}

Available tools:"""
        
        for tool_name, tool in self.tools.items():
            tool_def = tool.definition
            base_prompt += f"\n\n- {tool_name}: {tool_def.description}"
            base_prompt += "\n  Parameters:"
            for param in tool_def.parameters:
                required = " (required)" if param.required else " (optional)"
                base_prompt += f"\n    - {param.name} ({param.type}): {param.description}{required}"
        
        base_prompt += "\n\nAlways explain what you're doing when using tools and provide helpful context about the results."
        
        return base_prompt
    
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
        ollama_messages = [{"role": "system", "content": self.system_prompt}]
        
        for msg in messages:
            ollama_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        try:
            # Make request to Ollama
            async with self.client.stream(
                "POST",
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": ollama_messages,
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                
                full_response = ""
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                content = chunk["message"]["content"]
                                full_response += content
                                
                                # Yield content chunk
                                yield {
                                    "type": "content",
                                    "content": content,
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                # Check if response is done
                                if chunk.get("done", False):
                                    break
                        except json.JSONDecodeError:
                            continue
                
                # Process tool calls if any
                tool_calls = self._extract_tool_calls(full_response)
                for tool_call in tool_calls:
                    yield {
                        "type": "tool_call",
                        "tool": tool_call["tool"],
                        "parameters": tool_call["parameters"],
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Execute the tool
                    try:
                        result = await self._execute_tool(tool_call["tool"], tool_call["parameters"])
                        yield {
                            "type": "tool_result",
                            "tool": tool_call["tool"],
                            "result": result,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Generate follow-up response based on tool result
                        follow_up_messages = ollama_messages + [
                            {"role": "assistant", "content": full_response},
                            {"role": "user", "content": f"Tool {tool_call['tool']} returned: {json.dumps(result)}. Please provide a helpful summary or response based on this information."}
                        ]
                        
                        async with self.client.stream(
                            "POST",
                            f"{self.ollama_url}/api/chat",
                            json={
                                "model": self.model,
                                "messages": follow_up_messages,
                                "stream": True
                            }
                        ) as follow_response:
                            follow_response.raise_for_status()
                            
                            async for line in follow_response.aiter_lines():
                                if line.strip():
                                    try:
                                        chunk = json.loads(line)
                                        if "message" in chunk and "content" in chunk["message"]:
                                            content = chunk["message"]["content"]
                                            
                                            yield {
                                                "type": "content",
                                                "content": content,
                                                "timestamp": datetime.now().isoformat()
                                            }
                                            
                                            if chunk.get("done", False):
                                                break
                                    except json.JSONDecodeError:
                                        continue
                    
                    except Exception as e:
                        yield {
                            "type": "tool_error",
                            "tool": tool_call["tool"],
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }
                
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """Extract tool calls from the LLM response"""
        tool_calls = []
        
        # Pattern to match tool calls
        pattern = r'TOOL_CALL:\s*(\w+)\s*\nPARAMETERS:\s*(\{[^}]*\})'
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        
        for tool_name, params_str in matches:
            try:
                parameters = json.loads(params_str)
                if tool_name in self.tools:
                    tool_calls.append({
                        "tool": tool_name,
                        "parameters": parameters
                    })
            except json.JSONDecodeError:
                continue
        
        return tool_calls
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        return await tool.execute(**parameters)