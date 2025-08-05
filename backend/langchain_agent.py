"""LangChain-based agent implementation."""

import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_core.callbacks import AsyncCallbackHandler
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig

from models.model_manager import ModelManager
from models.providers.hybrid_function_caller import HybridFunctionCaller
from tools.langchain_tools import LangChainToolWrapper

logger = logging.getLogger(__name__)


class StreamingCallbackHandler(AsyncCallbackHandler):
    """Callback handler for streaming responses."""
    
    def __init__(self, callback_func):
        self.callback_func = callback_func
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Handle new token from LLM."""
        await self.callback_func({
            "type": "content",
            "content": token,
            "timestamp": datetime.now().isoformat()
        })


class LangChainAgent:
    """LangChain-based agent with support for multiple LLM providers."""
    
    def __init__(self, tools: Optional[List] = None, agent_type: str = "softcatala_english"):
        """Initialize the LangChain agent.
        
        Args:
            tools: List of tools to be used by the agent
            agent_type: Type of agent - "softcatala_english" (default) or "softcatala_catalan"
        """
        self.model_manager = ModelManager()
        self.tools = self._wrap_tools(tools or [])
        self.agent_executor = None
        self.agent_type = agent_type
        self._setup_agent()
    
    def _wrap_tools(self, tools: List) -> List[BaseTool]:
        """Wrap existing tools for LangChain compatibility."""
        wrapped_tools = []
        for tool in tools:
            if hasattr(tool, 'definition'):
                # Wrap existing tool
                wrapped_tool = LangChainToolWrapper(tool)
                wrapped_tools.append(wrapped_tool)
                logger.info(f"Wrapped tool: {wrapped_tool.name} - {wrapped_tool.description}")
                logger.debug(f"Tool schema: {wrapped_tool.args_schema}")
            else:
                # Assume it's already a LangChain tool
                wrapped_tools.append(tool)
                logger.info(f"Already LangChain tool: {getattr(tool, 'name', str(tool))}")
        
        logger.info(f"Total tools wrapped: {len(wrapped_tools)}")
        return wrapped_tools
    
    def _get_softcatala_english_prompt(self):
        """Get the Softcatalà agent prompt in English (for better LLM performance)."""
        return ChatPromptTemplate.from_messages([
            ("system", """# Softcatalà AI Assistant

You are a helpful AI Assistant from the Softcatalà non-profit association. Softcatalà has over 25 years of experience working to provide tools to navigate and experience information technologies in the Catalan language.

**Critical Requirement:** You will ONLY interact with users in Catalan language and will never resort to a different language. All your responses must be in Catalan.

## Your Main Task

Your main task is assistance in using technologies for translating and correcting Catalan texts that are provided by Softcatalà. These tools can be used via its website but you have direct access to them.

**When the user asks for support correcting or translating a text, ALWAYS resort to using a tool first in order to have the relevant context to provide an answer. Do not rely solely on your internal knowledge as you will be biased.**

## Available Tools

You have access to various tools that will be automatically available when needed. Use tools when necessary to provide accurate and helpful responses. Always explain your reasoning and provide context for your answers. Remember to respond in Catalan.

## How to Collaborate with Softcatalà

If a user asks how they can collaborate with Softcatalà, tell them the best way is to encourage the usage of Catalan language when using information technologies. They should switch the language of all their devices into Catalan and if not possible request the localization to the manufacturers via social media. They should encourage friends and family to do the same.
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def _get_softcatala_catalan_prompt(self):
        """Get the Softcatalà agent prompt in Catalan."""
        return ChatPromptTemplate.from_messages([
            ("system", """# Assistent d'IA de Softcatalà

Ets un assistent d'intel·ligència artificial útil de l'associació sense ànim de lucre Softcatalà. Softcatalà té més de 25 anys d'experiència treballant per proporcionar eines per navegar i experimentar les tecnologies de la informació en llengua catalana. 

**Important:** Només interactuaràs amb els usuaris en llengua catalana i mai no recorreràs a una llengua diferent.

## La teva tasca principal

La teva tasca principal és l'assistència en l'ús de tecnologies per traduir i corregir textos catalans que proporciona Softcatalà. Aquestes eines es poden utilitzar mitjançant el seu lloc web, però tu tens accés directe a elles.

**Quan l'usuari demani suport per corregir o traduir un text, SEMPRE recorre primer a utilitzar una eina per tenir el context rellevant per proporcionar una resposta. No et basïs únicament en el teu coneixement intern, ja que estaràs esbiaixat.**

## Eines disponibles

Tens accés a diverses eines que estaran disponibles automàticament quan sigui necessari. Utilitza aquestes eines quan sigui necessari per proporcionar respostes precises i útils. Explica sempre el teu raonament i proporciona context per a les teves respostes.

## Com col·laborar amb Softcatalà

Si un usuari pregunta com pot col·laborar amb Softcatalà, explica'li que la millor manera és fomentar l'ús de la llengua catalana quan s'utilitzen tecnologies de la informació. Han de canviar l'idioma de tots els seus dispositius al català i, si no és possible, sol·licitar la localització als fabricants via xarxes socials. Han d'animar amics i familiars a fer el mateix.
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])



    def _setup_agent(self):
        """Setup the LangChain agent with tools and prompts."""
        # Select prompt based on agent type
        if self.agent_type == "softcatala_catalan":
            prompt = self._get_softcatala_catalan_prompt()
            logger.info("Using Catalan prompt")
        else:
            # Default to Softcatalà English prompt (includes softcatala_english and any unknown types)
            prompt = self._get_softcatala_english_prompt()
            logger.info("Using English prompt")
        
        try:
            # Get the default model and provider
            llm = self.model_manager.get_default_model()
            provider = self.model_manager.get_provider_for_default_model()
            
            logger.info(f"Using LLM: {llm}")
            logger.info(f"Provider: {type(provider).__name__}")
            logger.info(f"LLM has bind_tools capability: {hasattr(llm, 'bind_tools')}")
            
            # Create agent if we have tools
            if self.tools:
                logger.info(f"Creating agent with {len(self.tools)} tools:")
                for tool in self.tools:
                    logger.info(f"  - {tool.name}: {tool.description}")
                    logger.debug(f"    Schema: {tool.args_schema}")
                
                # Check if this is OpenRouter provider and use hybrid approach
                if hasattr(provider, 'supports_native_function_calling'):
                    logger.info("Using OpenRouter provider with hybrid function calling")
                    self.hybrid_caller = HybridFunctionCaller(provider, llm, self.tools)
                    
                    # For OpenRouter, we'll handle function calling in chat_stream method
                    # For now, create a simple chain as fallback
                    self.agent_executor = prompt | llm
                    logger.info("Created hybrid function calling setup for OpenRouter")
                else:
                    # Use standard LangChain agent for other providers
                    agent = create_openai_tools_agent(llm, self.tools, prompt)
                    logger.info("OpenAI tools agent created successfully")
                    
                    self.agent_executor = AgentExecutor(
                        agent=agent,
                        tools=self.tools,
                        verbose=True,
                        handle_parsing_errors=True,
                        max_iterations=3
                    )
                    logger.info("AgentExecutor created successfully")
                    self.hybrid_caller = None
                
                logger.info(f"Agent executor type: {type(self.agent_executor)}")
            else:
                # Simple chain without tools
                self.agent_executor = prompt | llm
                self.hybrid_caller = None
                logger.info("Created simple chain without tools")
                
        except Exception as e:
            logger.error(f"Failed to setup agent: {e}")
            logger.exception("Full traceback:")
            raise
    
    async def chat_stream(self, messages: List[Dict], session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat responses using LangChain.
        
        Args:
            messages: List of message dictionaries
            session_id: Session identifier
            
        Yields:
            Dictionary containing response chunks
        """
        try:
            # Convert messages to LangChain format
            chat_history = []
            current_input = ""
            
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user" or role == "human":
                    if not current_input:  # Use the last human message as input
                        current_input = content
                    else:
                        chat_history.append(HumanMessage(content=content))
                elif role == "assistant" or role == "ai":
                    chat_history.append(AIMessage(content=content))
                elif role == "system":
                    chat_history.append(SystemMessage(content=content))
            
            if not current_input:
                yield {
                    "type": "error",
                    "error": "No user input found",
                    "timestamp": datetime.now().isoformat()
                }
                return
            
            # Prepare input for the agent
            agent_input = {
                "input": current_input,
                "chat_history": chat_history
            }
            
            # Configure streaming callback
            streaming_callback = StreamingCallbackHandler(
                lambda chunk: self._emit_chunk(chunk)
            )
            
            config = RunnableConfig(
                callbacks=[streaming_callback],
                tags=["streaming"],
                metadata={"session_id": session_id}
            )
            
            # Check if we should use hybrid function calling for OpenRouter
            if hasattr(self, 'hybrid_caller') and self.hybrid_caller:
                try:
                    logger.info("Using hybrid function caller for OpenRouter")
                    # Convert messages to LangChain format for hybrid caller
                    langchain_messages = []
                    for msg in [{"role": "system", "content": "You are a helpful assistant."}] + messages:
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        
                        if role == "user" or role == "human":
                            langchain_messages.append(HumanMessage(content=content))
                        elif role == "assistant" or role == "ai":
                            langchain_messages.append(AIMessage(content=content))
                        elif role == "system":
                            langchain_messages.append(SystemMessage(content=content))
                    
                    response = await self.hybrid_caller.call_with_tools(langchain_messages)
                    
                    yield {
                        "type": "content",
                        "content": response.content,
                        "timestamp": datetime.now().isoformat()
                    }
                    return
                    
                except Exception as e:
                    logger.error(f"Hybrid function calling failed: {e}, falling back to regular agent")
            
            if hasattr(self.agent_executor, 'astream'):
                # Stream with agent executor
                logger.info("Starting agent streaming...")
                logger.debug(f"Agent input: {agent_input}")
                try:
                    chunk_count = 0
                    async for chunk in self.agent_executor.astream(agent_input, config=config):
                        chunk_count += 1
                        logger.debug(f"Received chunk #{chunk_count}: {chunk}")
                        logger.debug(f"Chunk type: {type(chunk)}")
                        logger.debug(f"Chunk keys: {list(chunk.keys()) if isinstance(chunk, dict) else 'N/A'}")
                        
                        processed_chunk = await self._process_agent_chunk(chunk)
                        if processed_chunk:
                            logger.debug(f"Processed chunk: {processed_chunk}")
                            yield processed_chunk
                        else:
                            logger.debug("Chunk processed but no output generated")
                    
                    logger.info(f"Agent streaming completed. Total chunks processed: {chunk_count}")
                except Exception as stream_error:
                    logger.error(f"Error during agent streaming: {stream_error}")
                    logger.exception("Full streaming error traceback:")
                    yield {
                        "type": "error",
                        "error": f"Streaming error: {str(stream_error)}",
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                # Fallback to regular invoke
                try:
                    response = await self.agent_executor.ainvoke(agent_input, config=config)
                    yield {
                        "type": "content",
                        "content": response.get("output", str(response)),
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as invoke_error:
                    logger.error(f"Error during agent invoke: {invoke_error}")
                    yield {
                        "type": "error",
                        "error": f"Agent execution error: {str(invoke_error)}",
                        "timestamp": datetime.now().isoformat()
                    }
                
        except Exception as e:
            logger.error(f"Error in chat_stream: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _emit_chunk(self, chunk: Dict[str, Any]):
        """Emit a chunk to the stream."""
        # This is called by the streaming callback
        pass
    
    async def _process_agent_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Process a chunk from the agent executor."""
        # Log the chunk for debugging
        logger.debug(f"Processing agent chunk: {chunk}")
        logger.debug(f"Chunk type: {type(chunk)}")
        
        # Handle different types of chunks from LangChain agent
        if "output" in chunk:
            logger.info(f"Found output chunk: {chunk['output']}")
            return {
                "type": "content",
                "content": chunk["output"],
                "timestamp": datetime.now().isoformat()
            }
        elif "intermediate_steps" in chunk:
            # Handle tool calls
            steps = chunk["intermediate_steps"]
            logger.info(f"Found intermediate_steps chunk with {len(steps)} steps")
            for i, step in enumerate(steps):
                logger.debug(f"Step {i}: {step}")
                if len(step) >= 2:
                    action, observation = step[0], step[1]
                    logger.info(f"Tool execution - Action: {action.tool}, Input: {action.tool_input}, Result: {observation}")
                    # Emit tool result with tool name and result
                    return {
                        "type": "tool_result",
                        "tool": action.tool,
                        "input": action.tool_input,
                        "result": observation,
                        "timestamp": datetime.now().isoformat()
                    }
        elif "actions" in chunk:
            # Handle tool selection/calling phase
            actions = chunk["actions"]
            logger.info(f"Found actions chunk with {len(actions)} actions")
            for action in actions:
                logger.info(f"Tool call - Tool: {action.tool}, Input: {action.tool_input}")
                return {
                    "type": "tool_call",
                    "tool": action.tool,
                    "input": action.tool_input,
                    "timestamp": datetime.now().isoformat()
                }
        
        # Handle LangChain agent step types and tool usage
        if isinstance(chunk, dict):
            # Check for agent-related keys that indicate tool usage
            chunk_keys = set(chunk.keys())
            logger.debug(f"🔧 Chunk keys found: {chunk_keys}")
            
            # Check for tool_calls in the chunk (OpenAI tools format)
            if "tool_calls" in chunk_keys:
                tool_calls = chunk["tool_calls"]
                logger.info(f"🔧 Direct tool_calls found: {tool_calls}")
                if tool_calls and len(tool_calls) > 0:
                    tool_call = tool_calls[0]  # Take first tool call
                    return {
                        "type": "tool_call",
                        "tool": tool_call.get("function", {}).get("name", "unknown"),
                        "input": tool_call.get("function", {}).get("arguments", {}),
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Look for LangChain agent step patterns
            if "agent" in chunk_keys:
                agent_data = chunk["agent"]
                logger.debug(f"🔧 Agent data: {agent_data}")
                if isinstance(agent_data, dict):
                    # Check for tool calls in agent data
                    if "tool_calls" in agent_data:
                        tool_calls = agent_data["tool_calls"]
                        logger.info(f"🔧 Tool calls in agent data: {tool_calls}")
                        if tool_calls and len(tool_calls) > 0:
                            tool_call = tool_calls[0]
                            return {
                                "type": "tool_call",
                                "tool": tool_call.get("function", {}).get("name", "unknown"),
                                "input": tool_call.get("function", {}).get("arguments", {}),
                                "timestamp": datetime.now().isoformat()
                            }
                    
                    # Check for function calls (alternative format)
                    if "function_call" in agent_data:
                        function_call = agent_data["function_call"]
                        logger.info(f"🔧 Function call in agent data: {function_call}")
                        return {
                            "type": "tool_call",
                            "tool": function_call.get("name", "unknown"),
                            "input": function_call.get("arguments", {}),
                            "timestamp": datetime.now().isoformat()
                        }
            
            # Check for step-based execution
            if "steps" in chunk_keys:
                steps = chunk["steps"]
                logger.debug(f"🔧 Steps found: {steps}")
                if isinstance(steps, list) and steps:
                    last_step = steps[-1]
                    if isinstance(last_step, dict) and "action" in last_step:
                        action = last_step["action"]
                        logger.info(f"🔧 Action in step: {action}")
                        if hasattr(action, 'tool'):
                            return {
                                "type": "tool_call",
                                "tool": action.tool,
                                "input": getattr(action, 'tool_input', {}),
                                "timestamp": datetime.now().isoformat()
                            }
            
            # Look for messages or content with tool information
            if "messages" in chunk_keys:
                messages = chunk["messages"]
                logger.debug(f"🔧 Messages found: {messages}")
                if isinstance(messages, list) and messages:
                    last_msg = messages[-1]
                    logger.debug(f"🔧 Last message: {last_msg}")
                    
                    # Check for tool calls in message
                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                        tool_calls = last_msg.tool_calls
                        logger.info(f"🔧 Tool calls in message: {tool_calls}")
                        for tool_call in tool_calls:
                            return {
                                "type": "tool_call",
                                "tool": tool_call.get("name", "unknown"),
                                "input": tool_call.get("args", {}),
                                "timestamp": datetime.now().isoformat()
                            }
                    
                    # Regular message content
                    if hasattr(last_msg, 'content') and last_msg.content:
                        content = last_msg.content
                        # Check if content indicates tool usage
                        if "tool" in content.lower() or "function" in content.lower():
                            logger.debug(f"🔧 Message content with tool reference: {content}")
                        return {
                            "type": "content",
                            "content": content,
                            "timestamp": datetime.now().isoformat()
                        }
        
        # Default case for any unhandled chunks
        # Only return content if there's meaningful information
        chunk_str = str(chunk)
        if chunk_str and chunk_str not in ["", "{}", "[]", "None"]:
            return {
                "type": "content",
                "content": chunk_str,
                "timestamp": datetime.now().isoformat()
            }
        
        # Return None for empty/meaningless chunks
        return None
    
    async def check_health(self) -> Dict[str, Any]:
        """Check the health of the agent and its dependencies."""
        health_status = {
            "agent": "healthy",
            "timestamp": datetime.now().isoformat()
        }
        
        # Check model manager health
        try:
            model_health = await self.model_manager.health_check()
            health_status["models"] = model_health
        except Exception as e:
            health_status["models"] = {"error": str(e)}
            health_status["agent"] = "unhealthy"
        
        # Check tools
        health_status["tools"] = {
            "count": len(self.tools),
            "names": [tool.name for tool in self.tools]
        }
        
        # Add agent type information
        health_status["agent_type"] = self.agent_type
        
        return health_status
    
    async def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models from all providers."""
        return self.model_manager.list_available_models()
    
    def switch_model(self, provider: str, model_name: str, **kwargs):
        """Switch to a different model.
        
        Args:
            provider: Model provider (ollama, zhipu)
            model_name: Name of the model
            **kwargs: Additional model parameters
        """
        try:
            # Get the new model
            new_model = self.model_manager.get_model(provider, model_name, **kwargs)
            
            # Recreate the agent with the new model using the same prompt selection logic
            if self.agent_type == "softcatala_catalan":
                prompt = self._get_softcatala_catalan_prompt()
            else:
                # Default to Softcatalà English prompt (includes softcatala_english and any unknown types)
                prompt = self._get_softcatala_english_prompt()
            
            if self.tools:
                agent = create_openai_tools_agent(new_model, self.tools, prompt)
                self.agent_executor = AgentExecutor(
                    agent=agent,
                    tools=self.tools,
                    verbose=True,
                    handle_parsing_errors=True,
                    max_iterations=3
                )
            else:
                self.agent_executor = prompt | new_model
                
            logger.info(f"Switched to model {model_name} from provider {provider}")
            
        except Exception as e:
            logger.error(f"Failed to switch model: {e}")
            raise