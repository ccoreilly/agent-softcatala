from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
import logging
import asyncio
from dotenv import load_dotenv

from langchain_agent import LangChainAgent
from tools.catalan_synonyms import CatalanSynonymsTool
from tools.catalan_spell_checker import CatalanSpellCheckerTool
from tools.catalan_syllabification import CatalanSyllabificationTool
from tools.catalan_translator import CatalanTranslatorTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load .env file only if it exists
env_file_path = ".env"
if os.path.exists(env_file_path):
    load_dotenv(env_file_path)
    logger.info(f"Loaded environment variables from {env_file_path}")
else:
    logger.info("No .env file found, using system environment variables only")

# Validate that at least one LLM provider is configured
def validate_providers():
    """Validate that at least one LLM provider is properly configured."""
    ollama_url = os.getenv("OLLAMA_URL")
    zhipu_api_key = os.getenv("ZHIPUAI_API_KEY")
    openai_key = os.getenv("OPENAI_KEY")
    
    if not ollama_url and not zhipu_api_key and not openai_key:
        error_msg = (
            "No LLM providers configured. Please set at least one of:\n"
            "- OLLAMA_URL (for Ollama provider)\n"
            "- ZHIPUAI_API_KEY (for Zhipu AI provider)\n"
            "- OPENAI_KEY (for OpenAI provider)"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Log which providers are configured
    configured_providers = []
    if ollama_url:
        configured_providers.append(f"Ollama ({ollama_url})")
    if zhipu_api_key:
        configured_providers.append("Zhipu AI")
    if openai_key:
        configured_providers.append("OpenAI")
    
    logger.info(f"Configured providers: {', '.join(configured_providers)}")

# Validate providers before starting the application
validate_providers()

app = FastAPI(title="API de l'Agent de Softcatalà", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent with tools
# Agent type can be: "softcatala_english" (default) or "softcatala_catalan"
agent_type = os.getenv("AGENT_TYPE", "softcatala_english")
logger.info(f"Initializing agent with type: {agent_type}")

try:
    # Legacy tool - DISABLED
    # web_browser_tool = WebBrowserTool()
    
    # LangChain native tools - DISABLED  
    # search_tool = create_search_tool()
    # wikipedia_tool = create_wikipedia_tool()
    
    # New Catalan tools
    catalan_synonyms_tool = CatalanSynonymsTool()
    catalan_spell_checker_tool = CatalanSpellCheckerTool()
    catalan_syllabification_tool = CatalanSyllabificationTool()
    catalan_translator_tool = CatalanTranslatorTool()

    # Initialize LangChain agent with selected type - DISABLED TOOLS
    # agent = LangChainAgent(tools=[web_browser_tool, search_tool, wikipedia_tool], agent_type=agent_type)
    agent = LangChainAgent(tools=[catalan_synonyms_tool, catalan_spell_checker_tool, catalan_syllabification_tool, catalan_translator_tool], agent_type=agent_type)
    logger.info(f"LangChain agent initialized successfully with type: {agent_type}")
    
except Exception as e:
    logger.error(f"Failed to initialize agent: {e}")
    # Initialize without tools as fallback
    agent = LangChainAgent(tools=[], agent_type=agent_type)
    logger.warning(f"Agent initialized without tools with type: {agent_type}")

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: str
    provider: Optional[str] = None  # ollama, zhipu
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class ToolCall(BaseModel):
    tool: str
    input: Dict[str, Any]
    output: Any

class ChatResponse(BaseModel):
    message: ChatMessage
    tool_calls: Optional[List[ToolCall]] = None

class ModelInfo(BaseModel):
    provider: str
    models: List[str]
    status: str

@app.get("/")
async def root():
    return {
        "message": "API de l'Agent de Softcatalà",
        "status": "funcionant",
        "version": "2.0.0",
        "features": ["ollama", "zhipu_ai", "langchain", "tools", "telegram_bot"]
    }

@app.get("/health")
async def health():
    """Health check endpoint with detailed status."""
    try:
        health_status = await agent.check_health()
        return health_status
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Servei no saludable: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat responses from the Softcatalà agent."""
    try:
        # Switch model if requested
        if request.provider and request.model:
            model_kwargs = {}
            if request.temperature is not None:
                model_kwargs["temperature"] = request.temperature
            if request.max_tokens is not None:
                model_kwargs["max_tokens"] = request.max_tokens
            
            agent.switch_model(request.provider, request.model, **model_kwargs)
        
        # Convert Pydantic models to dictionaries
        messages_dict = [msg.dict() for msg in request.messages]
        
        async def generate():
            try:
                async for chunk in agent.chat_stream(messages_dict, request.session_id):
                    yield f"data: {json.dumps(chunk)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                error_chunk = {
                    "type": "error",
                    "error": str(e),
                    "timestamp": "2024-01-01T00:00:00"
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )
    except Exception as e:
        logger.error(f"Error in chat_stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_available_models():
    """Get list of available models from all providers."""
    try:
        models = await agent.get_available_models()
        
        # Format response
        providers = []
        for provider_name, model_list in models.items():
            providers.append(ModelInfo(
                provider=provider_name,
                models=model_list,
                status="disponible" if model_list else "no disponible"
            ))
        
        return {"providers": providers}
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/switch")
async def switch_model(request: Dict[str, Any]):
    """Switch to a different model."""
    try:
        provider = request.get("provider")
        model_name = request.get("model")
        
        if not provider or not model_name:
            raise HTTPException(
                status_code=400,
                detail="Tant 'provider' com 'model' són necessaris"
            )
        
        # Extract model parameters
        model_kwargs = {}
        for key in ["temperature", "max_tokens", "top_p"]:
            if key in request:
                model_kwargs[key] = request[key]
        
        agent.switch_model(provider, model_name, **model_kwargs)
        
        return {
            "message": f"Canviat correctament a {model_name} de {provider}",
            "provider": provider,
            "model": model_name,
            "parameters": model_kwargs
        }
        
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools")
async def get_available_tools():
    """Get list of available tools."""
    try:
        health_status = await agent.check_health()
        tools_info = health_status.get("tools", {})
        
        return {
            "count": tools_info.get("count", 0),
            "tools": tools_info.get("names", []),
            "status": "disponible"
        }
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/providers")
async def get_providers():
    """Get information about available LLM providers."""
    try:
        health_status = await agent.check_health()
        models_info = health_status.get("models", {})
        
        providers_info = []
        for provider, info in models_info.items():
            if isinstance(info, dict):
                providers_info.append({
                    "name": provider,
                    "status": info.get("status", "unknown"),
                    "models": info.get("available_models", []),
                    "details": info
                })
        
        return {"providers": providers_info}
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def start_telegram_bot():
    """Start the Telegram bot if configured."""
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not telegram_token:
        logger.info("TELEGRAM_BOT_TOKEN not found, skipping Telegram bot startup")
        return
    
    try:
        from telegram_bot import TelegramBot
        
        # Get max user messages from environment (default 20)
        max_user_messages = int(os.getenv("TELEGRAM_MAX_USER_MESSAGES", "20"))
        
        telegram_bot = TelegramBot(telegram_token, agent, max_user_messages)
        await telegram_bot.start_bot()
        
    except ImportError:
        logger.error("python-telegram-bot not installed. Install with: pip install python-telegram-bot==21.0.1")
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")


async def start_services():
    """Start both HTTP server and Telegram bot."""
    # Check if we should run Telegram bot
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if telegram_token:
        logger.info("Starting both HTTP endpoint and Telegram bot...")
        
        # Start Telegram bot in background
        telegram_task = asyncio.create_task(start_telegram_bot())
        
        # Import uvicorn and start HTTP server
        import uvicorn
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # Start HTTP server in background
        http_task = asyncio.create_task(server.serve())
        
        # Wait for both services
        try:
            await asyncio.gather(telegram_task, http_task)
        except KeyboardInterrupt:
            logger.info("Shutting down services...")
        except Exception as e:
            logger.error(f"Error running services: {e}")
    else:
        logger.info("Starting HTTP endpoint only (no Telegram token provided)...")
        import uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )


if __name__ == "__main__":
    # Check if we need to run with asyncio (for Telegram bot)
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if telegram_token:
        # Run with asyncio to support Telegram bot
        asyncio.run(start_services())
    else:
        # Run only HTTP server
        import uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )