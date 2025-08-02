# LangChain Chat Agent Backend

A modern chat agent backend built with FastAPI and LangChain, supporting multiple LLM providers including Ollama (local) and Zhipu AI (cloud).

## Features

- **Multiple LLM Providers**: Support for Ollama (local) and Zhipu AI (cloud)
- **LangChain Integration**: Built on LangChain for robust agent capabilities
- **Tool Support**: Web browsing, search, and Wikipedia tools
- **Streaming Responses**: Real-time streaming chat responses
- **Model Switching**: Dynamic switching between different models and providers
- **Health Monitoring**: Comprehensive health checks for all providers
- **Extensible Architecture**: Easy to add new providers and tools

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Ollama Configuration
OLLAMA_URL=http://localhost:11434

# Zhipu AI Configuration (optional)
ZHIPUAI_API_KEY=your_zhipu_api_key_here

# Other settings...
```

### 3. Set up Ollama (for local models)

1. Install Ollama from [https://ollama.ai](https://ollama.ai)
2. Start Ollama service:
   ```bash
   ollama serve
   ```
3. Pull a model:
   ```bash
   ollama pull llama3.2
   ```

### 4. Set up Zhipu AI (optional)

1. Sign up at [https://open.bigmodel.cn](https://open.bigmodel.cn)
2. Get your API key
3. Add it to your `.env` file

## Running the Backend

### Development

```bash
python main.py
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t langchain-chat-agent .
docker run -p 8000:8000 --env-file .env langchain-chat-agent
```

## API Endpoints

### Core Endpoints

- `GET /` - API information and status
- `GET /health` - Comprehensive health check
- `POST /chat/stream` - Stream chat responses
- `GET /models` - List available models from all providers
- `POST /models/switch` - Switch to a different model
- `GET /tools` - List available tools
- `GET /providers` - Get provider information

### Example Usage

#### Chat with Streaming

```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "session_id": "test-session",
    "provider": "ollama",
    "model": "llama3.2"
  }'
```

#### Switch Model

```bash
curl -X POST "http://localhost:8000/models/switch" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "zhipu",
    "model": "glm-4",
    "temperature": 0.8
  }'
```

#### Get Available Models

```bash
curl "http://localhost:8000/models"
```

## Supported Providers

### Ollama (Local)

- **Models**: Any model available in your local Ollama installation
- **Advantages**: Privacy, no API costs, full control
- **Requirements**: Ollama service running locally

Popular models:
- `llama3.2` (recommended)
- `llama3.1`
- `mistral`
- `codellama`

### Zhipu AI (Cloud)

- **Models**: `glm-4`, `glm-4v`, `glm-3-turbo`
- **Advantages**: High performance, multimodal support (glm-4v)
- **Requirements**: API key from Zhipu AI

## Tools

The backend supports various tools for enhanced capabilities:

### Built-in Tools

1. **Web Browser Tool**: Browse and extract content from web pages
2. **DuckDuckGo Search**: Web search capabilities
3. **Wikipedia**: Search and retrieve Wikipedia articles

### Adding Custom Tools

To add a custom tool:

1. Create a tool class inheriting from `BaseTool`
2. Register it in the agent initialization
3. The tool will be automatically available to the LLM

Example:

```python
from tools.base import BaseTool, ToolDefinition, ToolParameter

class CustomTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="custom_tool",
            description="My custom tool",
            parameters=[
                ToolParameter(
                    name="input",
                    type="string",
                    description="Input parameter",
                    required=True
                )
            ]
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        # Tool implementation
        return {"result": "success"}
```

## Architecture

### Model Management

The `ModelManager` class handles multiple LLM providers:

```python
from models.model_manager import ModelManager

manager = ModelManager()
model = manager.get_model("ollama", "llama3.2")
```

### Provider System

Each provider implements the `BaseProvider` interface:

- `OllamaProvider`: Local Ollama integration
- `ZhipuProvider`: Zhipu AI cloud integration

### LangChain Integration

The agent uses LangChain's:
- `ChatOllama` for Ollama models
- `ChatZhipuAI` for Zhipu AI models
- Agent framework for tool calling
- Streaming capabilities

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_URL` | Ollama service URL | `http://localhost:11434` |
| `ZHIPUAI_API_KEY` | Zhipu AI API key | None |
| `DEFAULT_PROVIDER` | Default LLM provider | `ollama` |
| `DEFAULT_MODEL` | Default model name | `llama3.2` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

### Model Parameters

You can configure model parameters globally or per-request:

- `temperature`: Controls randomness (0.0 - 1.0)
- `max_tokens`: Maximum response length
- `top_p`: Nucleus sampling parameter

## Troubleshooting

### Common Issues

1. **Ollama not accessible**
   - Ensure Ollama service is running: `ollama serve`
   - Check the URL in your configuration
   - Verify firewall settings

2. **Zhipu AI authentication failed**
   - Check your API key
   - Ensure it's properly set in environment variables
   - Verify your account has sufficient credits

3. **Model not found**
   - For Ollama: Pull the model with `ollama pull <model-name>`
   - For Zhipu AI: Use supported model names (`glm-4`, `glm-3-turbo`)

4. **Tools not working**
   - Check internet connectivity for search tools
   - Verify tool permissions and configurations

### Logs

The backend provides detailed logging. Set `LOG_LEVEL=DEBUG` in your environment for verbose output.

## Performance

### Recommendations

1. **Local Development**: Use Ollama with smaller models (3B-7B parameters)
2. **Production**: Consider Zhipu AI for better performance and reliability
3. **Scaling**: Use multiple Ollama instances behind a load balancer
4. **Caching**: Implement response caching for repeated queries

### Monitoring

The `/health` endpoint provides comprehensive health information:

```json
{
  "agent": "healthy",
  "models": {
    "ollama": {
      "status": "healthy",
      "available_models": ["llama3.2", "mistral"]
    },
    "zhipu": {
      "status": "healthy",
      "available_models": ["glm-4", "glm-3-turbo"]
    }
  },
  "tools": {
    "count": 3,
    "names": ["web_browser", "search", "wikipedia"]
  }
}
```

## Development

### Project Structure

```
backend/
├── main.py                 # FastAPI application
├── langchain_agent.py      # Main agent implementation
├── models/                 # Model management
│   ├── model_manager.py    # Central model manager
│   └── providers/          # Provider implementations
├── tools/                  # Tool implementations
│   ├── base.py            # Base tool interface
│   ├── langchain_tools.py # LangChain tool wrappers
│   └── web_browser.py     # Web browser tool
├── requirements.txt        # Dependencies
└── .env.example           # Environment template
```

### Testing

Run tests (when available):

```bash
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.