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
    
    def __init__(self, tools: Optional[List] = None):
        """Initialize the LangChain agent.
        
        Args:
            tools: List of tools to be used by the agent
        """
        self.model_manager = ModelManager()
        self.tools = self._wrap_tools(tools or [])
        self.agent_executor = None
        self._setup_agent()
    
    def _wrap_tools(self, tools: List) -> List[BaseTool]:
        """Wrap existing tools for LangChain compatibility."""
        wrapped_tools = []
        for tool in tools:
            if hasattr(tool, 'definition'):
                # Wrap existing tool
                wrapped_tools.append(LangChainToolWrapper(tool))
            else:
                # Assume it's already a LangChain tool
                wrapped_tools.append(tool)
        return wrapped_tools
    
    def _setup_agent(self):
        """Setup the LangChain agent with tools and prompts."""
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """# Assistent d'IA de Softcatalà

Ets un assistent d'intel·ligència artificial útil de l'associació sense ànim de lucre Softcatalà. Softcatalà té més de 25 anys d'experiència treballant per proporcionar eines per navegar i experimentar les tecnologies de la informació en llengua catalana. 

**Important:** Només interactuaràs amb els usuaris en llengua catalana i mai no recorreràs a una llengua diferent.

## La teva tasca principal

La teva tasca principal és l'assistència en l'ús de tecnologies per traduir i corregir textos catalans que proporciona Softcatalà. Aquestes eines es poden utilitzar mitjançant el seu lloc web, però tu tens accés directe a elles.

**Quan l'usuari demani suport per corregir o traduir un text, SEMPRE recorre primer a utilitzar una eina per tenir el context rellevant per proporcionar una resposta. No et basïs únicament en el teu coneixement intern, ja que estaràs esbiaixat.**

## Eines disponibles

Tens accés a les següents eines:
{tools}

Descripcions de les eines:
{tool_names}

Utilitza aquestes eines quan sigui necessari per proporcionar respostes precises i útils. Explica sempre el teu raonament i proporciona context per a les teves respostes.

## Com col·laborar amb Softcatalà

Si un usuari pregunta com pot col·laborar amb Softcatalà, explica'li que la millor manera és fomentar l'ús de la llengua catalana quan s'utilitzen tecnologies de la informació. Han de canviar l'idioma de tots els seus dispositius al català i, si no és possible, sol·licitar la localització als fabricants via xarxes socials. Han d'animar amics i familiars a fer el mateix.
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        try:
            # Get the default model
            llm = self.model_manager.get_default_model()
            
            # Create agent if we have tools
            if self.tools:
                agent = create_openai_tools_agent(llm, self.tools, prompt)
                self.agent_executor = AgentExecutor(
                    agent=agent,
                    tools=self.tools,
                    verbose=True,
                    handle_parsing_errors=True,
                    max_iterations=3
                )
            else:
                # Simple chain without tools
                self.agent_executor = prompt | llm
                
        except Exception as e:
            logger.error(f"Failed to setup agent: {e}")
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
            
            if hasattr(self.agent_executor, 'astream'):
                # Stream with agent executor
                async for chunk in self.agent_executor.astream(agent_input, config=config):
                    yield await self._process_agent_chunk(chunk)
            else:
                # Fallback to regular invoke
                response = await self.agent_executor.ainvoke(agent_input, config=config)
                yield {
                    "type": "content",
                    "content": response.get("output", str(response)),
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
        # Handle different types of chunks from LangChain agent
        if "output" in chunk:
            return {
                "type": "content",
                "content": chunk["output"],
                "timestamp": datetime.now().isoformat()
            }
        elif "intermediate_steps" in chunk:
            # Handle tool calls
            steps = chunk["intermediate_steps"]
            for step in steps:
                if len(step) >= 2:
                    action, observation = step[0], step[1]
                    return {
                        "type": "tool_call",
                        "tool": action.tool,
                        "input": action.tool_input,
                        "output": observation,
                        "timestamp": datetime.now().isoformat()
                    }
        
        # Default case
        return {
            "type": "content",
            "content": str(chunk),
            "timestamp": datetime.now().isoformat()
        }
    
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
            
            # Recreate the agent with the new model
            prompt = ChatPromptTemplate.from_messages([
                ("system", """# Assistent d'IA de Softcatalà

Ets un assistent d'intel·ligència artificial útil de l'associació sense ànim de lucre Softcatalà. Softcatalà té més de 25 anys d'experiència treballant per proporcionar eines per navegar i experimentar les tecnologies de la informació en llengua catalana. 

**Important:** Només interactuaràs amb els usuaris en llengua catalana i mai no recorreràs a una llengua diferent.

## La teva tasca principal

La teva tasca principal és l'assistència en l'ús de tecnologies per traduir i corregir textos catalans que proporciona Softcatalà. Aquestes eines es poden utilitzar mitjançant el seu lloc web, però tu tens accés directe a elles.

**Quan l'usuari demani suport per corregir o traduir un text, SEMPRE recorre primer a utilitzar una eina per tenir el context rellevant per proporcionar una resposta. No et basïs únicament en el teu coneixement intern, ja que estaràs esbiaixat.**

## Eines disponibles

Tens accés a les següents eines:
{tools}

Descripcions de les eines:
{tool_names}

Utilitza aquestes eines quan sigui necessari per proporcionar respostes precises i útils. Explica sempre el teu raonament i proporciona context per a les teves respostes.

## Com col·laborar amb Softcatalà

Si un usuari pregunta com pot col·laborar amb Softcatalà, explica'li que la millor manera és fomentar l'ús de la llengua catalana quan s'utilitzen tecnologies de la informació. Han de canviar l'idioma de tots els seus dispositius al català i, si no és possible, sol·licitar la localització als fabricants via xarxes socials. Han d'animar amics i familiars a fer el mateix.
"""),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
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