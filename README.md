# Chat Agent - AI Assistant with Tools

A modern web-based chat application that allows you to interact with AI agents powered by open-source LLMs through Ollama. The agents have access to tools and can perform actions like web browsing.

## Features

- 🤖 **AI Agent Integration**: Powered by Ollama with configurable open-source models
- 🛠️ **Tool Support**: Extensible tool system with web browsing capabilities
- 💬 **Modern Chat UI**: Clean, responsive interface with real-time streaming
- 📚 **Session Management**: Local storage of chat sessions with full history
- 🎨 **Markdown Support**: Rich text rendering with syntax highlighting
- 🌐 **Tool Visualization**: Interactive displays for tool executions and results
- 🐳 **Docker Ready**: Full containerization with Docker Compose
- 🚀 **Production Ready**: Nginx-served frontend with Traefik labels

## Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 4GB RAM for model execution

### 1. Clone and Setup

```bash
git clone <your-repo>
cd chat-agent
cp .env.example .env
```

### 2. Start Services

```bash
docker-compose up -d
```

This will start:
- **Ollama** on port 11434
- **Backend API** on port 8000  
- **Frontend** on port 3000

### 3. Pull a Model

```bash
# Pull a model (this may take a few minutes)
docker exec ollama ollama pull llama2

# Or try other models:
# docker exec ollama ollama pull codellama
# docker exec ollama ollama pull mistral
# docker exec ollama ollama pull neural-chat
```

### 4. Access the Application

Open your browser and go to http://localhost:3000

## Configuration

### Environment Variables

Edit `.env` to configure your setup:

```bash
# LLM Model Configuration
LLM_MODEL=llama2                    # Choose your model
OLLAMA_URL=http://ollama:11434      # Ollama service URL
CORS_ORIGINS=http://localhost:3000  # Allowed origins

# Production (for Traefik)
# TRAEFIK_HOST=your-domain.com
```

### Available Models

Popular models you can use:

- `llama2` - General purpose (3.8GB)
- `codellama` - Code-focused (3.8GB) 
- `mistral` - Fast and efficient (4.1GB)
- `neural-chat` - Conversation optimized (4.1GB)
- `llama2:13b` - Larger model for better quality (7.3GB)

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │     Ollama      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (LLM Server)  │
│   Port 3000     │    │   Port 8000     │    │   Port 11434    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Components

- **Frontend**: React TypeScript app with local storage for chat sessions
- **Backend**: FastAPI server with streaming responses and tool execution
- **Agent**: LLM integration with tool calling capabilities
- **Tools**: Extensible system with web browsing tool included
- **Ollama**: Local LLM server for model inference

## API Documentation

### Endpoints

- `GET /` - API status
- `GET /health` - Health check with model info
- `POST /chat/stream` - Streaming chat endpoint
- `GET /models` - List available models

### Chat API Example

```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!", "timestamp": "2023-01-01T00:00:00Z"}
    ],
    "session_id": "session-123"
  }'
```

## Tool System

### Available Tools

#### Web Browser Tool
- **Name**: `web_browser`
- **Description**: Browse web pages and extract content
- **Parameters**:
  - `url` (required): URL to browse
  - `extract_links` (optional): Extract links from page
  - `max_content_length` (optional): Limit content length

### Adding Custom Tools

1. Create a new tool class in `backend/tools/`:

```python
from .base import BaseTool, ToolDefinition, ToolParameter

class MyCustomTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="my_tool",
            description="Description of what the tool does",
            parameters=[
                ToolParameter(
                    name="param1",
                    type="string", 
                    description="Parameter description",
                    required=True
                )
            ]
        )
    
    async def execute(self, **kwargs):
        # Tool implementation
        return {"result": "success"}
```

2. Register the tool in `backend/main.py`:

```python
from tools.my_custom_tool import MyCustomTool

my_tool = MyCustomTool()
agent = Agent(tools=[web_browser_tool, my_tool])
```

## Development

### Local Development

For development with hot reload:

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend  
cd frontend
npm install
npm start
```

### Project Structure

```
chat-agent/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main application
│   ├── agent.py            # Agent implementation
│   ├── tools/              # Tool implementations
│   │   ├── base.py         # Base tool class
│   │   └── web_browser.py  # Web browsing tool
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── hooks/         # Custom hooks
│   │   ├── utils/         # Utilities
│   │   └── types.ts       # TypeScript types
│   ├── package.json       # Node dependencies
│   └── Dockerfile        # Frontend container
├── docker-compose.yml     # Service orchestration
└── .env.example          # Environment template
```

## Production Deployment

### With Traefik

The services include Traefik labels for production deployment:

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.chat-frontend.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.chat-frontend.entrypoints=websecure"
      - "traefik.http.routers.chat-frontend.tls.certresolver=letsencrypt"
```

### Environment Variables for Production

```bash
LLM_MODEL=llama2
OLLAMA_URL=http://ollama:11434
CORS_ORIGINS=https://your-domain.com
TRAEFIK_HOST=your-domain.com
```

## Troubleshooting

### Common Issues

1. **Ollama not accessible**
   ```bash
   docker exec ollama ollama list  # Check if models are loaded
   docker logs ollama              # Check Ollama logs
   ```

2. **Frontend can't connect to backend**
   - Check CORS_ORIGINS in environment
   - Verify backend is running on port 8000

3. **Model not found**
   ```bash
   docker exec ollama ollama pull llama2  # Pull the model
   ```

4. **Out of memory**
   - Try smaller models like `mistral`
   - Increase Docker memory limit

### Performance Tips

- Use faster models like `mistral` for better response times
- Increase model context length for longer conversations
- Use SSD storage for faster model loading

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your tool or feature
4. Submit a pull request

## License

MIT License - see LICENSE file for details