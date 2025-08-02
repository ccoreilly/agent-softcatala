from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
from dotenv import load_dotenv

from agent import Agent
from tools.web_browser import WebBrowserTool

load_dotenv()

app = FastAPI(title="Chat Agent API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent with tools
web_browser_tool = WebBrowserTool()
agent = Agent(
    ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
    model=os.getenv("LLM_MODEL", "llama2"),
    tools=[web_browser_tool]
)

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: str

class ToolCall(BaseModel):
    tool: str
    input: Dict[str, Any]
    output: Any

class ChatResponse(BaseModel):
    message: ChatMessage
    tool_calls: Optional[List[ToolCall]] = None

@app.get("/")
async def root():
    return {"message": "Chat Agent API", "status": "running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Check if ollama is accessible
        await agent.check_health()
        return {"status": "healthy", "model": agent.model}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat responses from the agent"""
    try:
        async def generate():
            async for chunk in agent.chat_stream(request.messages, request.session_id):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_available_models():
    """Get list of available models from Ollama"""
    try:
        models = await agent.get_available_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)