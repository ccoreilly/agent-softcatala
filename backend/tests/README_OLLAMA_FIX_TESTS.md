# Tests for Ollama Initialization Fix

This directory contains comprehensive tests for the Ollama initialization fix that prevents unnecessary initialization attempts when `OLLAMA_URL` is not configured.

## Background

**Issue**: The application was initializing Ollama even when the `OLLAMA_URL` environment variable was not defined, leading to:
- Unnecessary connection attempts to `http://localhost:11434`
- Error logs: `Failed to list Ollama models: HTTPConnectionPool(host='localhost', port=11434): Max retries exceeded`
- Confusion when only other providers (like Zhipu AI) were configured

**Fix**: Modified `ModelManager._initialize_providers()` to only initialize Ollama when `OLLAMA_URL` is explicitly set and non-empty.

## Test Files

### 1. `test_model_manager_logic.py` - Logic Tests (✅ Ready to Run)

**Purpose**: Tests the core initialization logic without requiring heavy dependencies.

**What it tests**:
- OLLAMA_URL handling logic (not set, empty, whitespace, valid URL)
- Comparison between old behavior (with fallback) vs new behavior (no fallback)  
- Various provider initialization scenarios
- Regression test for the specific reported issue

**Run with**:
```bash
python3 -m pytest tests/test_model_manager_logic.py -v
# OR
python3 tests/test_model_manager_logic.py
```

**Key test cases**:
- `test_ollama_url_logic_without_fallback`: Core URL validation logic
- `test_old_vs_new_behavior`: Demonstrates the fix
- `test_regression_fix`: Exact scenario from the bug report

### 2. `test_model_manager_integration.py` - Integration Tests (⏸️ Requires Dependencies)

**Purpose**: Full integration tests that mock the actual ModelManager class.

**What it tests**:
- Full ModelManager initialization with mocked providers
- Log message verification
- Error handling during provider initialization
- Health check behavior with/without Ollama
- get_default_model fallback behavior

**Requirements**: 
- `langchain_core` and other LLM dependencies
- Install with: `pip install -r requirements.txt`

**Run with** (when dependencies available):
```bash
python3 -m pytest tests/test_model_manager_integration.py -v
```

**Key test cases**:
- `test_regression_ollama_not_initialized_without_url`: Main regression test
- `test_ollama_initialized_when_url_provided`: Positive case
- `test_get_default_model_without_ollama`: Fallback behavior

### 3. `test_model_manager.py` - Full Unit Tests (⏸️ Requires Dependencies)

**Purpose**: Comprehensive unit tests for all ModelManager functionality.

**What it tests**:
- Complete provider initialization scenarios
- Error handling and logging
- Model retrieval and health checks
- Integration between both test approaches

**Status**: Created but requires dependencies to run.

## Test Coverage

The tests cover these critical scenarios:

| Scenario | Logic Tests | Integration Tests |
|----------|-------------|------------------|
| OLLAMA_URL not set | ✅ | ✅ |
| OLLAMA_URL empty string | ✅ | ✅ |
| OLLAMA_URL whitespace only | ✅ | ✅ |
| OLLAMA_URL valid | ✅ | ✅ |
| Only Zhipu configured | ✅ | ✅ |
| Both providers configured | ✅ | ✅ |
| Provider initialization errors | ❌ | ✅ |
| Log message verification | ❌ | ✅ |
| Health check behavior | ❌ | ✅ |

## Running All Tests

### Quick verification (no dependencies required):
```bash
python3 -m pytest tests/test_model_manager_logic.py -v
```

### Full test suite (when dependencies available):
```bash
python3 -m pytest tests/test_model_manager*.py -v
```

### Test specific scenarios:
```bash
# Just the regression test
python3 -m pytest -k "regression" -v

# Just Ollama-related tests  
python3 -m pytest -k "ollama" -v

# Skip integration tests
python3 -m pytest tests/test_model_manager_logic.py -v
```

## Expected Behavior After Fix

### Before Fix (❌ Wrong):
```
2025-08-03 13:08:45,329 - models.model_manager - INFO - Initialized Ollama provider at http://localhost:11434
2025-08-03 13:08:45,419 - models.providers.ollama_provider - ERROR - Failed to list Ollama models: HTTPConnectionPool(host='localhost', port=11434): Max retries exceeded
```

### After Fix (✅ Correct):
```
2025-08-03 13:08:45,329 - models.model_manager - WARNING - OLLAMA_URL not found or empty, Ollama provider not initialized
2025-08-03 13:08:45,329 - models.model_manager - INFO - Initialized Zhipu AI provider
```

## Contributing

When adding new tests:

1. **Logic tests** (`test_model_manager_logic.py`): Add here for environment variable logic, simple behavior verification
2. **Integration tests** (`test_model_manager_integration.py`): Add here for testing with mocked ModelManager, log verification, error handling
3. **Full unit tests** (`test_model_manager.py`): Add here for comprehensive provider testing when dependencies are available

All tests should follow the pattern of cleaning up environment variables and using appropriate mocking.