# Backend Testing Suite

This directory contains comprehensive tests for the FastAPI backend application.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared fixtures and configuration
├── test_api.py              # FastAPI endpoint tests
├── test_integration.py      # Integration tests for components
├── test_health.py           # Health check and monitoring tests
└── README.md               # This file
```

## Test Categories

### 1. API Tests (`test_api.py`)
- **Root endpoint**: Basic functionality and version info
- **Health endpoint**: System health and status checks
- **Models endpoint**: Model management and switching
- **Tools endpoint**: Available tools and functionality
- **Providers endpoint**: LLM provider information
- **Chat streaming**: Chat functionality and error handling
- **Request validation**: Input validation and error responses

### 2. Integration Tests (`test_integration.py`)
- **LangChain Agent**: Agent initialization and functionality
- **Model Providers**: Ollama and Zhipu AI integration
- **Tools Integration**: Web browser, search, and Wikipedia tools
- **Message History**: Chat history management
- **Environment Configuration**: Settings and configuration
- **Error Handling**: Resilience and fallback behavior

### 3. Health Check Tests (`test_health.py`)
- **Service Availability**: Individual service health checks
- **System Metrics**: Performance and resource monitoring
- **Failure Scenarios**: Partial and complete failures
- **Resilience**: Timeout handling and recovery
- **Docker Integration**: Health check compatibility

## Running Tests

### Local Development

1. **Using the test runner script (recommended):**
   ```bash
   ./run_tests.sh
   ```

2. **Install dependencies and run manually:**
   
   **Using uv (recommended):**
   ```bash
   uv sync --dev
   uv run pytest tests/ -v
   ```
   
   **Using pip (legacy):**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   python -m pytest tests/ -v
   ```

3. **Run with coverage:**
   
   **Using uv:**
   ```bash
   uv run pytest tests/ -v --cov=. --cov-report=html
   ```
   
   **Using pip:**
   ```bash
   python -m pytest tests/ -v --cov=. --cov-report=html
   ```

4. **Run specific test categories:**
   ```bash
   # API tests only
   python -m pytest tests/test_api.py -v
   
   # Integration tests only
   python -m pytest tests/test_integration.py -v
   
   # Health tests only
   python -m pytest tests/test_health.py -v
   ```

### CI/CD Pipeline

Tests are automatically run in GitHub Actions on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

The CI pipeline includes:
1. Python setup and dependency installation
2. Code linting with flake8
3. Test execution with coverage reporting
4. Docker build verification

## Test Configuration

### Pytest Configuration (`pytest.ini`)
- Test discovery patterns
- Coverage settings
- Warning filters
- Custom markers

### Fixtures (`conftest.py`)
- Environment variable mocking
- Sample data for tests
- Async event loop configuration
- Test markers and configuration

## Mocking Strategy

Tests use comprehensive mocking to avoid external dependencies:

- **LangChain Agent**: Mocked to return predictable responses
- **Model Providers**: Mocked to simulate various availability scenarios
- **HTTP Requests**: Mocked to avoid actual API calls
- **Environment Variables**: Mocked for consistent test environment

## Coverage Goals

- **API Endpoints**: 100% coverage of all routes
- **Error Handling**: All error scenarios covered
- **Integration Points**: All external service interactions tested
- **Edge Cases**: Boundary conditions and failure modes

## Writing New Tests

### Naming Conventions
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Best Practices
1. Use descriptive test names that explain what is being tested
2. Follow the Arrange-Act-Assert pattern
3. Mock external dependencies
4. Test both success and failure scenarios
5. Use fixtures for common test data
6. Add appropriate markers (`@pytest.mark.integration`, etc.)

### Example Test Structure
```python
class TestNewFeature:
    """Test new feature functionality."""
    
    def test_feature_success_case(self, client, mock_dependency):
        """Test feature works correctly in normal conditions."""
        # Arrange
        expected_result = {"status": "success"}
        mock_dependency.return_value = expected_result
        
        # Act
        response = client.get("/new-feature")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == expected_result
    
    def test_feature_error_handling(self, client, mock_dependency):
        """Test feature handles errors gracefully."""
        # Arrange
        mock_dependency.side_effect = Exception("Test error")
        
        # Act
        response = client.get("/new-feature")
        
        # Assert
        assert response.status_code == 500
```

## Continuous Improvement

The test suite is designed to:
- Catch regressions early
- Ensure API reliability
- Validate system health
- Support safe refactoring
- Enable confident deployments

Regular maintenance includes:
- Updating tests for new features
- Reviewing coverage reports
- Optimizing test performance
- Adding integration scenarios