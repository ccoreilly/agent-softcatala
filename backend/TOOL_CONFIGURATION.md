# Tool Configuration Guide

## Current Status

The original agent tools have been **disabled** but kept in the codebase for easy re-enablement. They are commented out in `main.py`.

### Disabled Tools
- **WebBrowserTool**: Tool for browsing web pages and extracting content from URLs
- **DuckDuckGo Search**: Web search functionality  
- **Wikipedia Tool**: Wikipedia search and content retrieval

### Active Tools
- **CatalanSynonymsTool**: Tool for searching Catalan synonyms using the Softcatalà dictionary API
- **CatalanSpellCheckerTool**: Tool for checking Catalan text for spelling, grammar, and style errors using the Softcatalà corrector API

## Re-enabling Original Tools

To re-enable the original tools, edit `backend/main.py` and uncomment the following lines:

```python
# Legacy tool - DISABLED
web_browser_tool = WebBrowserTool()

# LangChain native tools - DISABLED  
search_tool = create_search_tool()
wikipedia_tool = create_wikipedia_tool()

# Initialize LangChain agent with selected type - DISABLED TOOLS
agent = LangChainAgent(tools=[web_browser_tool, search_tool, wikipedia_tool, catalan_synonyms_tool], agent_type=agent_type)
```

And comment out:
```python
# agent = LangChainAgent(tools=[catalan_synonyms_tool], agent_type=agent_type)
```

## Catalan Synonyms Tool

The `CatalanSynonymsTool` provides access to the Softcatalà dictionary API with three main functions:

1. **search**: Get synonyms for a word
2. **autocomplete**: Get word suggestions
3. **index**: Get words starting with a prefix

## Catalan Spell Checker Tool

The new `CatalanSpellCheckerTool` provides comprehensive spell and grammar checking for Catalan text using the Softcatalà corrector API with these features:

1. **Spelling correction**: Detects and suggests corrections for misspelled words
2. **Grammar checking**: Identifies grammatical errors with suggestions
3. **Dialect support**: Automatically detects or allows manual selection between standard Catalan and Valencian
4. **Detailed error analysis**: Categorizes errors by type (spelling, grammar, style, etc.)
5. **Context-aware suggestions**: Provides contextually appropriate correction suggestions

### Spell Checker Parameters:
- `text` (required): The Catalan text to check for errors
- `dialect` (optional): Catalan dialect - 'general', 'valencia', or 'auto' for automatic detection (default: 'auto')

### Synonyms Tool Actions:
1. **search**: Get synonyms and antonyms for a Catalan word
2. **autocomplete**: Get word suggestions for a given prefix  
3. **index**: Get words from the dictionary index starting with a prefix

### Parameters:
- `action` (required): "search", "autocomplete", or "index"
- `word` (required): The Catalan word or prefix to search
- `max_results` (optional): Maximum number of results for autocomplete/index (default: 10)

### Example Usage:
```python
# Search for synonyms
result = await tool.execute(action="search", word="casa")

# Get autocomplete suggestions
result = await tool.execute(action="autocomplete", word="cas", max_results=5)

# Get index words
result = await tool.execute(action="index", word="cas", max_results=10)
```

### API Endpoints Used:
- `https://api.softcatala.org/sinonims/v1/api/search/{word}`
- `https://api.softcatala.org/sinonims/v1/api/autocomplete/{prefix}`
- `https://api.softcatala.org/sinonims/v1/api/index/{prefix}`

## Dependencies

The Catalan Synonyms tool requires:
- `httpx` for HTTP requests
- `pydantic` for data validation

These are already included in `requirements.txt`.