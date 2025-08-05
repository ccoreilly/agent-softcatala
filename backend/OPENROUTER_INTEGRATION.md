# OpenRouter Provider Integration

This document describes the OpenRouter provider integration that has been added to the LangChain Chat Agent Backend.

## Overview

OpenRouter is a unified API that provides access to 100+ AI models from various providers including OpenAI, Anthropic, Google, Meta, Mistral, and many others. The integration allows users to access all these models through a single API key with automatic fallbacks and competitive pricing.

## Files Added/Modified

### New Files
- `models/providers/openrouter_provider.py` - Main OpenRouter provider implementation
- `tests/test_openrouter_provider.py` - Comprehensive test suite for the provider

### Modified Files
- `models/providers/__init__.py` - Added OpenRouterProvider export
- `models/model_manager.py` - Added OPENROUTER to ModelProvider enum and initialization logic
- `backend/README.md` - Updated documentation with OpenRouter configuration and usage

## Implementation Details

### Provider Features
- **Base Provider Compliance**: Implements all required methods from `BaseProvider`
- **Model Access**: Support for 100+ models through unified interface
- **Default Model**: Uses `google/gemma-3-27b-it:free` as the default (free model)
- **Attribution Support**: Optional site URL and name for OpenRouter rankings
- **Custom Endpoints**: Support for custom base URLs if needed
- **Health Monitoring**: Comprehensive health check implementation

### Configuration

The OpenRouter provider can be configured using the following environment variables:

- `OPENROUTER_API_KEY` (required) - Your OpenRouter API key
- `OPENROUTER_BASE_URL` (optional) - Custom base URL (defaults to https://openrouter.ai/api/v1)
- `OPENROUTER_SITE_URL` (optional) - Your site URL for OpenRouter attribution
- `OPENROUTER_SITE_NAME` (optional) - Your site name for OpenRouter attribution

### Model Fallback Priority

The ModelManager has been updated with the following fallback priority:
1. Ollama (if configured)
2. **OpenRouter (new)** - Uses free model by default
3. OpenAI (if configured)
4. Zhipu AI (if configured)

This ensures that if no local models are available, the system will fall back to OpenRouter's free model before trying paid services.

### Available Models

The provider includes a curated list of popular models:
- `google/gemma-3-27b-it:free` (default, free)
- `anthropic/claude-3-5-sonnet`
- `openai/gpt-4o`
- `openai/gpt-4o-mini`
- `meta-llama/llama-3.1-405b-instruct`
- `google/gemini-pro`
- `mistralai/mixtral-8x7b-instruct`
- And many more...

## Usage Examples

### Basic Setup
```bash
export OPENROUTER_API_KEY="your_api_key_here"
python3 main.py
```

### With Attribution
```bash
export OPENROUTER_API_KEY="your_api_key_here"
export OPENROUTER_SITE_URL="https://myapp.com"
export OPENROUTER_SITE_NAME="My Chat App"
python3 main.py
```

### API Usage
```bash
# Switch to OpenRouter provider
curl -X POST "http://localhost:8000/models/switch" \
  -H "Content-Type: application/json" \
  -d '{"provider": "openrouter", "model": "google/gemma-3-27b-it:free"}'

# List available models
curl "http://localhost:8000/models/"
```

## Benefits

1. **Cost Efficiency**: Access to free models like Gemma 3 27B
2. **Model Diversity**: 100+ models from different providers
3. **Automatic Fallbacks**: Built-in redundancy if one provider fails
4. **Unified Interface**: Single API for all models
5. **Competitive Pricing**: Often cheaper than direct provider APIs
6. **Easy Integration**: Uses existing OpenAI-compatible interface

## Testing

Comprehensive tests have been included in `tests/test_openrouter_provider.py`:
- Provider initialization and configuration
- Model retrieval and parameter handling
- Attribution header management
- Health check functionality
- Error handling
- Environment variable handling

To run tests (after installing dependencies):
```bash
python -m pytest tests/test_openrouter_provider.py -v
```

## Security Considerations

- API key is loaded from environment variables (never hardcoded)
- Attribution headers are optional and configurable
- Custom endpoints supported for enterprise deployments
- Error handling prevents API key leakage in logs

## Future Enhancements

Potential future improvements:
1. Dynamic model list fetching from OpenRouter API
2. Model pricing information integration
3. Usage analytics and cost tracking
4. Model performance metrics
5. Provider-specific optimizations

## Compatibility

The OpenRouter provider is fully compatible with:
- Existing LangChain agent workflows
- Telegram bot integration
- Streaming responses
- Tool calling capabilities
- Message history management
- Health monitoring systems