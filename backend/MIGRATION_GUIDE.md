# Migration Guide: From Custom Agent to LangChain

This guide explains the changes made to upgrade the backend from a custom agent implementation to a LangChain-based system with support for multiple LLM providers.

## What Changed

### 🔄 Backend Architecture

**Before:**
- Custom `Agent` class with direct Ollama HTTP calls
- Single LLM provider (Ollama only)
- Custom tool interface
- Basic streaming implementation

**After:**
- LangChain-based `LangChainAgent` 
- Multiple LLM providers (Ollama + Zhipu AI)
- LangChain tool ecosystem integration
- Advanced streaming with proper callbacks
- Modular provider system

### 📁 File Structure Changes

**New Files:**
```
backend/
├── langchain_agent.py          # NEW: LangChain-based agent
├── models/                     # NEW: Model management system
│   ├── __init__.py
│   ├── model_manager.py        # Central model manager
│   └── providers/              # Provider implementations
│       ├── __init__.py
│       ├── base_provider.py    # Base provider interface
│       ├── ollama_provider.py  # Ollama integration
│       └── zhipu_provider.py   # Zhipu AI integration
├── tools/
│   └── langchain_tools.py      # NEW: LangChain tool wrappers
├── .env.example                # NEW: Environment template
├── README.md                   # NEW: Comprehensive documentation
├── MIGRATION_GUIDE.md          # NEW: This file
└── start.sh                    # NEW: Quick start script
```

**Modified Files:**
- `main.py` - Updated to use LangChain agent
- `requirements.txt` - Added LangChain dependencies
- `Dockerfile` - Enhanced for LangChain support

**Preserved Files:**
- `tools/base.py` - Tool interface (unchanged)
- `tools/web_browser.py` - Web browser tool (unchanged)

### 🔧 Dependencies

**New Dependencies:**
```
langchain==0.3.0
langchain-core==0.3.0
langchain-community==0.3.0
langchain-ollama==0.2.0
httpx-sse==0.4.0
PyJWT==2.8.0
pypdf==3.17.0
chromadb==0.4.15
```

## Migration Steps

### 1. Backup Your Current Setup

```bash
# Backup your current backend
cp -r backend backend_backup
```

### 2. Install New Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your settings
```

### 4. API Changes

The API endpoints have been enhanced but remain backward compatible:

**New Endpoints:**
- `POST /models/switch` - Switch between models/providers
- `GET /providers` - Get provider information
- `GET /tools` - List available tools

**Enhanced Endpoints:**
- `POST /chat/stream` - Now supports provider/model selection
- `GET /models` - Returns models from all providers
- `GET /health` - More detailed health information

### 5. Update Client Code

If you have frontend or client code, update requests to take advantage of new features:

**Before:**
```javascript
// Old API call
const response = await fetch('/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    messages: [...],
    session_id: 'session123'
  })
});
```

**After:**
```javascript
// New API call with provider selection
const response = await fetch('/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    messages: [...],
    session_id: 'session123',
    provider: 'ollama',          // NEW: Choose provider
    model: 'llama3.2',          // NEW: Choose model
    temperature: 0.7            // NEW: Model parameters
  })
});
```

## Configuration Guide

### Environment Variables

Update your `.env` file with the new configuration options:

```bash
# Ollama Configuration (existing)
OLLAMA_URL=http://localhost:11434

# Zhipu AI Configuration (new)
ZHIPUAI_API_KEY=your_api_key_here

# Model Preferences (new)
DEFAULT_PROVIDER=ollama
DEFAULT_MODEL=llama3.2
DEFAULT_TEMPERATURE=0.7
```

### Provider Setup

#### Ollama (Local)
1. Install Ollama: https://ollama.ai
2. Start service: `ollama serve`
3. Pull models: `ollama pull llama3.2`

#### Zhipu AI (Cloud)
1. Sign up: https://open.bigmodel.cn
2. Get API key from dashboard
3. Add to `.env`: `ZHIPUAI_API_KEY=your_key`

## Feature Comparison

| Feature | Before | After |
|---------|--------|-------|
| LLM Providers | Ollama only | Ollama + Zhipu AI |
| Model Switching | Manual config change | Runtime API calls |
| Tool System | Custom interface | LangChain ecosystem |
| Streaming | Basic implementation | Advanced with callbacks |
| Health Checks | Simple Ollama ping | Comprehensive multi-provider |
| Documentation | Minimal | Comprehensive with examples |
| Error Handling | Basic | Robust with detailed logging |

## Benefits of Migration

### 🚀 Performance
- Better streaming implementation
- Optimized model loading
- Efficient provider management

### 🔧 Flexibility
- Switch between local and cloud models
- Runtime model configuration
- Easy provider addition

### 🛠 Developer Experience
- LangChain ecosystem access
- Better error messages
- Comprehensive documentation
- Quick start scripts

### 🔒 Reliability
- Robust error handling
- Health monitoring
- Graceful fallbacks

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Solution: Install dependencies
   pip install -r requirements.txt
   ```

2. **Ollama Connection Failed**
   ```bash
   # Solution: Check Ollama service
   ollama serve
   curl http://localhost:11434/api/tags
   ```

3. **Zhipu AI Authentication**
   ```bash
   # Solution: Check API key
   echo $ZHIPUAI_API_KEY
   ```

4. **Model Not Found**
   ```bash
   # For Ollama: Pull the model
   ollama pull llama3.2
   
   # For Zhipu: Use correct model names
   # glm-4, glm-4v, glm-3-turbo
   ```

### Rollback Plan

If you encounter issues, you can rollback:

```bash
# Stop new backend
# Restore backup
rm -rf backend
mv backend_backup backend
```

## Support

- Check the detailed `README.md` for comprehensive documentation
- Use the `start.sh` script for quick setup
- Review logs for detailed error information
- Test with the `/health` endpoint for system status

## Next Steps

After migration:

1. **Test All Features**: Verify chat, streaming, and tool functionality
2. **Configure Providers**: Set up both Ollama and Zhipu AI
3. **Update Documentation**: Update any internal documentation
4. **Monitor Performance**: Use health endpoints for monitoring
5. **Explore New Features**: Try model switching and new tools

The migration provides a solid foundation for future enhancements and better user experience!