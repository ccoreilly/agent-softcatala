from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
import logging
from dotenv import load_dotenv

from langchain_agent import LangChainAgent
from tools.web_browser import WebBrowserTool
from tools.langchain_tools import create_search_tool, create_wikipedia_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="LangChain Chat Agent API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent with tools
try:
    # Legacy tool
    web_browser_tool = WebBrowserTool()
    
    # LangChain native tools
    search_tool = create_search_tool()
    wikipedia_tool = create_wikipedia_tool()
    
    # Initialize LangChain agent
    agent = LangChainAgent(tools=[web_browser_tool, search_tool, wikipedia_tool])
    logger.info("LangChain agent initialized successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize agent: {e}")
    # Initialize without tools as fallback
    agent = LangChainAgent(tools=[])
    logger.warning("Agent initialized without tools")

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
        "message": "LangChain Chat Agent API",
        "status": "running",
        "version": "2.0.0",
        "features": ["ollama", "zhipu_ai", "langchain", "tools"]
    }

@app.get("/health")
async def health():
    """Health check endpoint with detailed status."""
    try:
        health_status = await agent.check_health()
        return health_status
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat responses from the LangChain agent."""
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
                status="available" if model_list else "unavailable"
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
                detail="Both 'provider' and 'model' are required"
            )
        
        # Extract model parameters
        model_kwargs = {}
        for key in ["temperature", "max_tokens", "top_p"]:
            if key in request:
                model_kwargs[key] = request[key]
        
        agent.switch_model(provider, model_name, **model_kwargs)
        
        return {
            "message": f"Successfully switched to {model_name} from {provider}",
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
            "status": "available"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )