# LangChain Chat Agent Backend

A powerful backend service that provides LLM-powered chat capabilities through both REST API and Telegram bot interfaces. Built with FastAPI and integrated with LangChain for advanced tool usage and multi-provider model support.

## Features

- **Multi-Provider LLM Support**: Supports Ollama, Zhipu AI, OpenAI, OpenRouter, and other providers
- **Tool Integration**: Web browsing, Wikipedia search, and extensible tool system
- **Streaming Responses**: Real-time response streaming for better user experience  
- **Model Switching**: Dynamic switching between different models and providers
- **Telegram Bot**: Full-featured Telegram bot with conversation history
- **Message History Management**: Rolling window conversation history (up to 20 user messages)
- **Health Monitoring**: Comprehensive health checks and status reporting

## Quick Start

### Environment Variables

You can configure the application in three ways:

#### Option 1: Environment Variables (Recommended for production)
```bash
# Set environment variables directly
export OLLAMA_URL=http://localhost:11434
# OR
export ZHIPUAI_API_KEY=your_zhipu_api_key
# OR
export OPENAI_KEY=your_openai_api_key
# OR
export OPENROUTER_API_KEY=your_openrouter_api_key

# Optional configurations
export CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://ccoreilly.github.io
export TELEGRAM_BOT_TOKEN=your_telegram_bot_token
export TELEGRAM_MAX_USER_MESSAGES=20
export SEARCH_API_KEY=your_search_api_key

# Start the application
python3 main.py
```

#### Option 2: .env file (Recommended for development)
Create a `.env` file in the backend directory:

```bash
# Copy the template
cp .env.example .env

# Edit .env with your settings
# At minimum, set ONE of these:
OLLAMA_URL=http://localhost:11434
# OR
ZHIPUAI_API_KEY=your_zhipu_api_key
# OR
OPENAI_KEY=your_openai_api_key
# OR
OPENROUTER_API_KEY=your_openrouter_api_key

# Optional: Use custom endpoint (normally not needed)
# Z.AI and Zhipu AI use the same API endpoint by default
# ZHIPUAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# Optional: CORS configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://ccoreilly.github.io

# Optional: Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_MAX_USER_MESSAGES=20

# Optional: Search tool configuration
SEARCH_API_KEY=your_search_api_key
```

#### Option 3: Inline environment variables
```bash
# Quick start with Ollama
OLLAMA_URL=http://localhost:11434 python3 main.py

# Quick start with Zhipu AI
ZHIPUAI_API_KEY=your_api_key python3 main.py
```

**Important**: At least one of `OLLAMA_URL`, `ZHIPUAI_API_KEY`, `OPENAI_KEY`, or `OPENROUTER_API_KEY` must be set for the application to start.

### Installation

#### Option 1: Using uv (Recommended)

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or
   pip install uv
   ```

2. **Install Dependencies**:
   ```bash
   # Create virtual environment and install dependencies (recommended)
   uv sync
   
   # Alternative: Create environment and install with pip-style commands
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

3. **Start the Service**:
   ```bash
   # If using uv sync (recommended)
   uv run python main.py
   
   # Or if virtual environment is activated
   python main.py
   ```

#### Option 2: Using pip (Legacy)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Service**:
   ```bash
   python main.py
   ```

The service will automatically:
- Start the HTTP API on port 8000
- Start the Telegram bot (if `TELEGRAM_BOT_TOKEN` is provided)
- Initialize available LLM providers and tools

## API Endpoints

### Core Endpoints

- `GET /` - Service information and status
- `GET /health` - Detailed health check with provider status
- `POST /chat/stream` - Stream chat responses (SSE format)
- `GET /models` - List available models from all providers
- `POST /models/switch` - Switch active model
- `GET /tools` - List available tools
- `GET /providers` - Provider status and capabilities

### Chat Streaming

The `/chat/stream` endpoint supports Server-Sent Events (SSE) for real-time streaming:

```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "session_id": "test_session",
    "provider": "ollama",
    "model": "llama2"
  }'
```

Response chunks:
```json
{"type": "content", "content": "Hello! I'm doing well...", "timestamp": "2024-01-01T12:00:00"}
{"type": "tool_call", "tool": "search", "parameters": {...}, "timestamp": "2024-01-01T12:00:01"}
{"type": "tool_result", "tool": "search", "result": {...}, "timestamp": "2024-01-01T12:00:02"}
```

## Z.AI Integration

The system now supports Z.AI (formerly Zhipu AI) with their latest GLM models. Z.AI offers OpenAI-compatible API endpoints with competitive pricing and performance.

### Configuration
Set the following environment variable:
```bash
ZHIPUAI_API_KEY=your_z_ai_api_key
```

The system automatically uses the correct Z.AI/Zhipu API endpoint. No additional configuration needed.

### Models
- **Default**: GLM-4.5-flash (fast, efficient, and cost-effective)
- **Available models**:
  - `glm-4.5-flash` - New default: fast, efficient, and optimized for most tasks
  - `glm-4.5-air` - Lightweight model with excellent performance
  - `glm-4.5` - Flagship model with maximum capabilities
  - `glm-4`, `glm-4-plus`, `glm-4-flash` - Previous generation models
  - `glm-3-turbo` - Legacy model

### Features
- **Hybrid Reasoning**: Supports both thinking mode (complex reasoning) and non-thinking mode (instant responses)

## OpenRouter Integration

OpenRouter provides access to 100+ AI models through a single API, including Claude, GPT-4, Gemini, and many open-source models. It offers automatic fallbacks, competitive pricing, and access to free models.

### Configuration
Set the following environment variable:
```bash
OPENROUTER_API_KEY=your_openrouter_api_key
```

Optional configuration for attribution and tracking:
```bash
OPENROUTER_SITE_URL=https://yoursite.com     # Your site URL (for OpenRouter rankings)
OPENROUTER_SITE_NAME="Your App Name"         # Your app name (for OpenRouter rankings)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1  # Custom endpoint (usually not needed)
```

### Models
- **Default**: `google/gemma-3-27b-it:free` (free model, no cost)
- **Popular models available**:
  - `google/gemma-3-27b-it:free` - Free Gemma model (default)
  - `anthropic/claude-3-5-sonnet` - Latest Claude model
  - `openai/gpt-4o` - GPT-4 Omni
  - `openai/gpt-4o-mini` - Smaller, faster GPT-4
  - `meta-llama/llama-3.1-405b-instruct` - Large Llama model
  - `google/gemini-pro` - Google's Gemini Pro
  - `mistralai/mixtral-8x7b-instruct` - Mistral's mixture model
  - And 100+ more models

### Features
- **Free Models**: Access to several free models with no API costs
- **Automatic Fallbacks**: If one provider is down, automatically switches to backup
- **Unified Interface**: Access all models through a single API
- **Cost Optimization**: Automatically routes to the most cost-effective provider
- **Tool Integration**: Native function calling capabilities for agent applications
- **128K Context**: Extended context length for long conversations
- **Streaming Support**: Real-time response streaming
- **Cost Effective**: Competitive pricing with high performance

### API Compatibility
The Z.AI provider is compatible with OpenAI-style chat completions and supports all standard parameters like temperature, max_tokens, etc.

### Testing Your Configuration
Run the included test script to verify your Z.AI setup:
```bash
python test_zai.py
```

This script will:
- Verify your API key and endpoint configuration
- Test the GLM-4.5-flash model
- Perform a health check
- Confirm all functionality is working

### Endpoint Configuration
By default, the system uses the standard Zhipu AI endpoint. To use the Z.AI endpoint as documented at docs.z.ai:

```bash
export ZHIPUAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"
```

Or add to your `.env` file:
```
ZHIPUAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
```

### Model Features
- **GLM-4.5-flash**: Ultra-fast inference, optimized for real-time applications
- **GLM-4.5**: Full-featured model with advanced reasoning capabilities  
- **GLM-4.5-air**: Lightweight version with balanced performance and efficiency

## Telegram Bot

### Setup

1. **Create a Telegram Bot**:
   - Contact [@BotFather](https://t.me/BotFather) on Telegram
   - Create a new bot with `/newbot`
   - Copy the bot token

2. **Configure Environment**:
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_MAX_USER_MESSAGES=20  # Optional, defaults to 20
   ```

3. **Start the Service**:
   ```bash
   python main.py
   ```

### Bot Commands

- `/start` - Welcome message and introduction
- `/help` - Detailed help and command reference
- `/clear` - Clear conversation history
- `/history` - Show conversation statistics
- `/status` - Check bot and AI model status

### Message History Management

The Telegram bot maintains conversation context with a rolling window approach:

- **Rolling Window**: Keeps the last 20 user messages (configurable)
- **Context Preservation**: All agent responses between user messages are preserved
- **Automatic Cleanup**: Older messages are automatically removed when limit is exceeded
- **Per-User Storage**: Each Telegram user has independent message history
- **Memory Efficient**: History is stored in memory and cleaned up automatically

Example conversation flow:
```
User: "Hello" → Stored (user message #1)
Bot: "Hi there! How can I help?" → Stored (agent response)
User: "What's the weather?" → Stored (user message #2)
Bot: "I'll search for weather info..." → Stored (agent response)
... (continues until 20 user messages)
User: "New question" → Stored (user message #21)
    → Message #1 and its responses are removed
    → Messages #2-21 and their responses are kept
```

### Bot Features

- **Real-time Streaming**: Messages are updated in real-time as the AI generates responses
- **Tool Usage Indicators**: Shows when tools are being used (web search, etc.)
- **Error Handling**: Graceful error handling with user-friendly messages
- **Typing Indicators**: Shows typing status while processing
- **Markdown Support**: Supports basic Markdown formatting in responses
- **Concurrent Safety**: Prevents message processing conflicts per user

## Model Providers

### Ollama (Local)

Supports local Ollama installations:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2

# Configure backend
OLLAMA_URL=http://localhost:11434
```

### Zhipu AI (Cloud)

Supports Zhipu AI's commercial API:

```bash
ZHIPU_API_KEY=your_api_key
```

## Tool System

### Available Tools

1. **Web Browser Tool**: Browse and extract content from web pages
2. **Search Tool**: Web search capabilities (requires API key)
3. **Wikipedia Tool**: Search and retrieve Wikipedia content

### Adding Custom Tools

Tools are automatically discovered from the `tools/` directory. Create new tools by:

1. Inheriting from `BaseTool`
2. Implementing required methods
3. Adding to the tools list in `main.py`

Example tool structure:
```python
from tools.base import BaseTool

class CustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="Description of what the tool does",
            parameters=[...]
        )
    
    async def execute(self, **kwargs):
        # Tool implementation
        return {"result": "tool output"}
```

## Configuration

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OLLAMA_URL` | Ollama service URL | `http://localhost:11434` | No |
| `ZHIPU_API_KEY` | Zhipu AI API key | None | No |
| `OPENAI_KEY` | OpenAI API key | None | No |
| `OPENAI_BASE_URL` | Custom OpenAI base URL | None | No |
| `OPENROUTER_API_KEY` | OpenRouter API key | None | No |
| `OPENROUTER_BASE_URL` | Custom OpenRouter base URL | `https://openrouter.ai/api/v1` | No |
| `OPENROUTER_SITE_URL` | Your site URL (for OpenRouter attribution) | None | No |
| `OPENROUTER_SITE_NAME` | Your site name (for OpenRouter attribution) | None | No |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000` | No |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | None | No |
| `TELEGRAM_MAX_USER_MESSAGES` | Max user messages in history | `20` | No |
| `SEARCH_API_KEY` | Search API key for web search | None | No |

### Running Options

1. **HTTP Only** (no Telegram token):
   ```bash
   python main.py  # Starts only HTTP API
   ```

2. **HTTP + Telegram Bot**:
   ```bash
   TELEGRAM_BOT_TOKEN=your_token python main.py  # Starts both services
   ```

3. **Docker**:
   ```bash
   docker build -t langchain-backend .
   docker run -p 8000:8000 -e TELEGRAM_BOT_TOKEN=your_token langchain-backend
   ```

## Health Monitoring

The `/health` endpoint provides comprehensive status information:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "models": {
    "ollama": {
      "status": "available",
      "available_models": ["llama2", "codellama"],
      "current_model": "llama2"
    },
    "zhipu": {
      "status": "configured",
      "available_models": ["glm-4", "glm-3-turbo"]
    }
  },
  "tools": {
    "count": 3,
    "names": ["web_browser", "search", "wikipedia"]
  }
}
```

## Logging

The backend provides detailed logging for monitoring and debugging:

- **INFO Level**: Service startup, model switches, successful requests
- **ERROR Level**: Service errors, model failures, tool errors
- **DEBUG Level**: Detailed request/response information (when enabled)

Log format:
```
2024-01-01 12:00:00,000 - langchain_agent - INFO - Agent initialized successfully
2024-01-01 12:00:01,000 - telegram_bot - INFO - Started conversation with user 12345
```

## Troubleshooting

### Common Issues

1. **Ollama Connection Failed**:
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Start Ollama if needed
   ollama serve
   ```

2. **Model Not Found**:
   ```bash
   # List available models
   ollama list
   
   # Pull required model
   ollama pull llama2
   ```

3. **Telegram Bot Not Responding**:
   - Verify bot token is correct
   - Check bot is not already running elsewhere
   - Ensure network connectivity to Telegram API

4. **Tools Not Working**:
   - Check API keys for search tools
   - Verify network connectivity for web tools
   - Check tool configuration in logs

### Performance Tuning

- **Memory Usage**: Adjust `TELEGRAM_MAX_USER_MESSAGES` for memory optimization
- **Response Speed**: Use faster models for quicker responses
- **Concurrent Users**: Monitor resource usage with multiple Telegram users

## Development

### Development Setup with uv

For development, we recommend using `uv` for faster dependency management:

```bash
# Clone the repository
git clone https://github.com/softcatala/agent-softcatala.git
cd agent-softcatala/backend

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies (including dev dependencies)
uv sync --dev

# Run the development server
uv run python main.py

# Run tests
uv run pytest

# Run linting
uv run black .
uv run isort .
uv run flake8 .
uv run mypy .
```

### Adding Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Update dependencies
uv sync
```

### Project Structure

```
backend/
├── main.py                 # Main service entry point
├── langchain_agent.py      # LangChain agent implementation
├── telegram_bot.py         # Telegram bot implementation
├── message_history.py      # Message history management
├── tools/                  # Tool implementations
│   ├── base.py            # Base tool interface
│   ├── web_browser.py     # Web browsing tool
│   └── langchain_tools.py # LangChain tool wrappers
├── models/                 # Model configurations
├── requirements.txt        # Dependencies
└── README.md              # This file
```

### Contributing

1. Follow existing code patterns and documentation
2. Add comprehensive error handling
3. Include logging for debugging
4. Test with both HTTP API and Telegram bot
5. Update documentation for new features

## License

This project is licensed under the MIT License - see the LICENSE file for details.