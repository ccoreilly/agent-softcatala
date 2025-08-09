# Chat Agent - AI Assistant with Tools

A modern web-based chat application that allows you to interact with AI agents powered by open-source LLMs through Ollama. The agents have access to tools and can perform actions like web browsing.

## Features

- 🤖 **AI Agent Integration**: Powered by Ollama with configurable open-source models
- 🛠️ **Native Tool Support**: Uses Ollama's built-in tool calling API for reliable function execution
- 💬 **Modern Chat UI**: Clean, responsive interface with real-time streaming
- 📚 **Session Management**: Local storage of chat sessions with full history
- 🎨 **Markdown Support**: Rich text rendering with syntax highlighting
- 🌐 **Tool Visualization**: Interactive displays for tool executions and results
- ⚡ **Streaming Tools**: Real-time tool execution with streaming responses
- 🐳 **Docker Ready**: Full containerization with Docker Compose
- 🚀 **Production Ready**: Nginx-served frontend with Traefik labels

## Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 4GB RAM for model execution

> **⚡ New in v2.0**: Native Ollama tool calling support! The agent now uses Ollama's built-in function calling API for more reliable and faster tool execution with streaming support.

### 1. Clone and Setup

```bash
git clone <your-repo>
cd chat-agent

# Option 1: Create .env file (recommended for development)
cp .env.example .env
# Edit .env with your configuration

# Option 2: Use environment variables directly (recommended for production)
export OLLAMA_URL=http://ollama:11434
# OR
export ZHIPUAI_API_KEY=your_zhipu_api_key
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
docker exec ollama ollama pull llama3.2

# Or try other models with tool support:
# docker exec ollama ollama pull llama3.1
# docker exec ollama ollama pull qwen2.5
```

### 4. Access the Application

Open your browser and go to http://localhost:3000

## Configuration

### Environment Variables

You can configure the application using environment variables directly or with a `.env` file. At minimum, you need **one** of the following LLM providers:

#### Required (at least one):
```bash
# For local Ollama instance
OLLAMA_URL=http://ollama:11434

# OR for Zhipu AI cloud service
ZHIPUAI_API_KEY=your_zhipu_api_key
```

#### Optional configuration:
Edit `.env` to configure additional options:

```bash
# LLM Model Configuration
LLM_MODEL=llama3.2                  # Choose your model
OLLAMA_URL=http://ollama:11434      # Ollama service URL
CORS_ORIGINS=http://localhost:3000,https://ccoreilly.github.io  # Allowed origins

# Agent Configuration
AGENT_TYPE=softcatala_english       # Agent type: softcatala_english (default) or softcatala_catalan

# Production (for Traefik)
# TRAEFIK_HOST=your-domain.com
```

### Agent Types

The system supports two different Softcatalà agent types that can be configured using the `AGENT_TYPE` environment variable:

#### 🏴‍☠️ softcatala_english (Default)
- **System Prompt**: English (for better LLM performance)
- **Response Language**: Catalan only
- **Purpose**: Optimized Softcatalà assistant with English instructions for better model comprehension
- **Best For**: Production use with Catalan language support

#### 🏴‍☠️ softcatala_catalan  
- **System Prompt**: Catalan
- **Response Language**: Catalan only
- **Purpose**: Fully Catalan Softcatalà assistant 
- **Best For**: Testing prompt effectiveness in Catalan vs English

**Usage Examples:**
```bash
# Use default Softcatalà agent (English prompt, Catalan responses)
AGENT_TYPE=softcatala_english

# Use fully Catalan Softcatalà agent
AGENT_TYPE=softcatala_catalan
```

### Available Models

Popular models you can use:

- `llama3.1` - Latest model with native tool support (4.7GB) ⭐
- `llama3.2` - Efficient with tool calling (2.0GB) ⭐
- `qwen2.5` - Advanced model with excellent tool support (4.4GB) ⭐
- `mistral` - Fast and efficient (4.1GB)
- `codellama` - Code-focused (3.8GB)
- `llama2:13b` - Larger model for better quality (7.3GB)

⭐ **Recommended for tool usage** - These models have native training for function calling and provide the best experience with tools.

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

**Note**: Tools are now integrated using Ollama's native tool calling API instead of prompt-based approaches, providing better reliability and streaming support.

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
LLM_MODEL=llama3.2
OLLAMA_URL=http://ollama:11434
CORS_ORIGINS=https://your-domain.com
TRAEFIK_HOST=your-domain.com
AGENT_TYPE=softcatala_english
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
   docker exec ollama ollama pull llama3.2  # Pull the model
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