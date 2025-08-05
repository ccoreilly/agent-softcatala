# OpenRouter Hybrid Function Calling Implementation

## Overview

This implementation provides a sophisticated hybrid approach to function calling with OpenRouter models, combining native function calling support (for models that support it) with a text-based fallback mechanism (inspired by Philipp Schmid's approach) for models that don't.

## Problem Solved

The original issue was that not all OpenRouter models support native function calling. Instead of limiting ourselves to only function-calling capable models, this hybrid approach:

1. **Keeps Gemma 3 as default** - Uses the free `google/gemma-3-27b-it:free` model
2. **Implements fallback function calling** - Uses text-based function calling for models without native support
3. **Maintains native support** - Uses standard function calling for models that support it
4. **Provides unified interface** - Same API regardless of the underlying approach

## Architecture

### Core Components

1. **OpenRouterProvider** - Enhanced with model capability detection
2. **HybridFunctionCaller** - Intelligent wrapper that chooses the appropriate approach
3. **LangChain Agent Integration** - Seamless integration with existing agent framework

### Function Calling Detection

Models are categorized into two groups:

#### Native Function Calling Models
- Anthropic Claude models (3.5 Sonnet, 3.5 Haiku, etc.)
- OpenAI GPT models (GPT-4o, GPT-4 Turbo, etc.)
- Google Gemini models (Pro 1.5, Flash 1.5, etc.)
- Mistral models (Large, Mixtral series)
- Cohere Command models

#### Fallback Function Calling Models  
- Google Gemma models (including Gemma 3)
- Meta Llama models
- Qwen models
- DeepSeek models
- And many others

## Text-Based Function Calling Approach

Following Philipp Schmid's methodology from his [Gemma function calling article](https://www.philschmid.de/gemma-function-calling):

### 1. Special Prompt Format
```
At each turn, if you decide to invoke any of the function(s), it should be wrapped with ```tool_code```. The python methods described below are imported and available, you can only use defined methods...

The following Python methods are available:

```python
def get_weather(location: str):
    """Get the current weather for a location."""
```

User: What's the weather in Paris?
```

### 2. Model Response with Tool Call
```
I'll check the weather in Paris for you.

```tool_code
get_weather(location="Paris")
```
```

### 3. Tool Execution and Response
```
```tool_output
The weather in Paris is sunny and 22°C.
```

Based on the weather data, Paris is currently experiencing sunny weather with a temperature of 22°C.
```

## Implementation Details

### HybridFunctionCaller Class

```python
class HybridFunctionCaller:
    def __init__(self, provider, model, tools):
        # Automatically detects model capabilities
        self.supports_native = provider.supports_native_function_calling(model_name)
        
    async def call_with_tools(self, messages):
        if self.supports_native and self.tools:
            return await self._call_with_native_tools(messages)
        elif self.tools:
            return await self._call_with_fallback_tools(messages)
        else:
            return await self.model.ainvoke(messages)
```

### Function Call Parsing

The text-based approach uses regex to extract function calls:

```python
def _extract_tool_call_from_text(self, text: str):
    pattern = r"```tool_code\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    # Parse function_name(arg1=value1, arg2=value2) format
```

### LangChain Integration

The agent automatically detects OpenRouter providers and uses the hybrid approach:

```python
if hasattr(provider, 'supports_native_function_calling'):
    self.hybrid_caller = HybridFunctionCaller(provider, llm, self.tools)
    # Use hybrid calling in chat_stream method
```

## Benefits

### 1. **Cost-Effective Default**
- Uses free Gemma 3 model by default
- No API costs for basic testing and development
- Scales to paid models when needed

### 2. **Maximum Model Compatibility** 
- Works with 50+ OpenRouter models
- Automatic capability detection
- Graceful fallback between approaches

### 3. **Unified Developer Experience**
- Same tool definition format
- Same API interface
- Transparent switching between modes

### 4. **Production Ready**
- Error handling and fallbacks
- Logging and debugging support
- Performance optimized

## Usage Examples

### Basic Tool Definition
```python
@tool
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    return f"The weather in {location} is sunny and 22°C."

@tool  
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b
```

### Model Selection
```python
# Free model with fallback function calling
model = provider.get_model("google/gemma-3-27b-it:free")

# Paid model with native function calling  
model = provider.get_model("anthropic/claude-3-5-haiku")

# Hybrid caller works with both
hybrid_caller = HybridFunctionCaller(provider, model, tools)
```

### Agent Integration
```python
# Automatically uses hybrid approach for OpenRouter
agent = LangChainAgent(tools=[get_weather, add_numbers])
```

## Testing

Run the comprehensive test suite:

```bash
cd /workspace/backend
python test_hybrid_function_calling.py
```

Tests cover:
- Native vs fallback detection
- Function call parsing
- Tool execution
- Error handling
- Multiple model types

## Model Recommendations

### Development/Testing
- `google/gemma-3-27b-it:free` - Free, good instruction following
- `google/gemini-flash-1.5:free` - Free, native function calling
- `mistralai/mistral-7b-instruct:free` - Free, good performance

### Production
- `anthropic/claude-3-5-haiku` - Excellent function calling, cost-effective
- `openai/gpt-4o-mini` - Fast, reliable, good value
- `google/gemini-flash-1.5` - Fast, multimodal, good pricing

## Monitoring and Debugging

### Health Check Enhancements
```python
{
    "status": "healthy",
    "default_model": "google/gemma-3-27b-it:free",
    "native_function_calling_models": 25,
    "fallback_function_calling_supported": True,
    "available_models_count": 45
}
```

### Logging
- Model capability detection
- Function calling mode selection
- Tool execution results
- Fallback triggers

## Future Enhancements

1. **Caching** - Cache model capability detection
2. **Metrics** - Track success rates by approach
3. **Auto-scaling** - Automatic model selection based on load
4. **Custom Prompts** - Model-specific prompt optimization

## References

- [Philipp Schmid's Gemma Function Calling Guide](https://www.philschmid.de/gemma-function-calling)
- [OpenRouter Tool Calling Documentation](https://openrouter.ai/docs/features/tool-calling)
- [OpenRouter Models with Tool Support](https://openrouter.ai/models?supported_parameters=tools)
- [LangChain Tools Documentation](https://python.langchain.com/docs/modules/tools/)