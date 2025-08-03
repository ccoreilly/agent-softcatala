"""
Integration tests for ModelManager class.
These tests require the full dependencies to be installed.
"""

import pytest
import os
import logging
from unittest.mock import patch, MagicMock

# These imports will only work when dependencies are installed
try:
    from models.model_manager import ModelManager, ModelProvider
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE,
    reason="ModelManager dependencies not available"
)


@pytest.fixture
def clean_environment():
    """Fixture that ensures a clean environment for each test."""
    original_env = {}
    env_vars_to_clean = ['OLLAMA_URL', 'ZHIPUAI_API_KEY']
    
    # Save original values
    for var in env_vars_to_clean:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]
    
    yield
    
    # Restore original values
    for var in env_vars_to_clean:
        if var in os.environ:
            del os.environ[var]
        if var in original_env:
            os.environ[var] = original_env[var]


class TestModelManagerOllamaInitializationFix:
    """Integration tests for the Ollama initialization fix."""
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_regression_ollama_not_initialized_without_url(
        self, mock_zhipu, mock_ollama, clean_environment, caplog
    ):
        """
        Regression test: Ensure Ollama is not initialized when OLLAMA_URL is not set.
        
        This is the exact scenario from the bug report:
        - OLLAMA_URL is not set
        - Only ZHIPUAI_API_KEY is configured
        - Ollama should NOT be initialized (preventing connection errors)
        """
        # Set up the exact scenario from the bug report
        os.environ['ZHIPUAI_API_KEY'] = 'test-key'
        
        # Mock Zhipu provider
        mock_zhipu_instance = MagicMock()
        mock_zhipu.return_value = mock_zhipu_instance
        
        # Create ModelManager
        with caplog.at_level(logging.INFO):
            manager = ModelManager()
        
        # CRITICAL: Ollama should NOT be initialized
        mock_ollama.assert_not_called()
        assert ModelProvider.OLLAMA not in manager.providers
        
        # Only Zhipu should be initialized
        mock_zhipu.assert_called_once_with('test-key')
        assert ModelProvider.ZHIPU in manager.providers
        
        # Check expected log messages
        assert "OLLAMA_URL not found or empty, Ollama provider not initialized" in caplog.text
        assert "Initialized Zhipu AI provider" in caplog.text
        
        # Most importantly: No Ollama connection error logs should appear
        assert "Failed to list Ollama models" not in caplog.text
        assert "HTTPConnectionPool" not in caplog.text
        assert "Connection refused" not in caplog.text
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')  
    def test_ollama_initialized_when_url_provided(
        self, mock_zhipu, mock_ollama, clean_environment, caplog
    ):
        """Test that Ollama IS initialized when OLLAMA_URL is explicitly set."""
        # Set OLLAMA_URL
        test_url = 'http://localhost:11434'
        os.environ['OLLAMA_URL'] = test_url
        
        # Mock Ollama provider
        mock_ollama_instance = MagicMock()
        mock_ollama.return_value = mock_ollama_instance
        
        # Create ModelManager
        with caplog.at_level(logging.INFO):
            manager = ModelManager()
        
        # Ollama should be initialized with the correct URL
        mock_ollama.assert_called_once_with(test_url)
        assert ModelProvider.OLLAMA in manager.providers
        assert manager.providers[ModelProvider.OLLAMA] == mock_ollama_instance
        
        # Check expected log message
        assert f"Initialized Ollama provider at {test_url}" in caplog.text
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_ollama_not_initialized_with_empty_url(
        self, mock_zhipu, mock_ollama, clean_environment, caplog
    ):
        """Test that Ollama is not initialized when OLLAMA_URL is empty."""
        # Set OLLAMA_URL to empty string
        os.environ['OLLAMA_URL'] = ''
        
        # Create ModelManager
        with caplog.at_level(logging.WARNING):
            manager = ModelManager()
        
        # Ollama should not be initialized
        mock_ollama.assert_not_called()
        assert ModelProvider.OLLAMA not in manager.providers
        
        # Check expected log message
        assert "OLLAMA_URL not found or empty, Ollama provider not initialized" in caplog.text
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_ollama_not_initialized_with_whitespace_url(
        self, mock_zhipu, mock_ollama, clean_environment, caplog
    ):
        """Test that Ollama is not initialized when OLLAMA_URL contains only whitespace."""
        # Set OLLAMA_URL to whitespace
        os.environ['OLLAMA_URL'] = '   \t\n  '
        
        # Create ModelManager
        with caplog.at_level(logging.WARNING):
            manager = ModelManager()
        
        # Ollama should not be initialized
        mock_ollama.assert_not_called()
        assert ModelProvider.OLLAMA not in manager.providers
        
        # Check expected log message
        assert "OLLAMA_URL not found or empty, Ollama provider not initialized" in caplog.text
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_ollama_initialization_error_handled_gracefully(
        self, mock_zhipu, mock_ollama, clean_environment, caplog
    ):
        """Test that Ollama initialization errors are handled gracefully."""
        # Set OLLAMA_URL
        os.environ['OLLAMA_URL'] = 'http://localhost:11434'
        
        # Make OllamaProvider raise an exception
        mock_ollama.side_effect = Exception("Connection failed")
        
        # Create ModelManager (should not crash)
        with caplog.at_level(logging.WARNING):
            manager = ModelManager()
        
        # Ollama should be attempted but fail gracefully
        mock_ollama.assert_called_once()
        assert ModelProvider.OLLAMA not in manager.providers
        
        # Check that warning was logged
        assert "Failed to initialize Ollama provider" in caplog.text
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_get_default_model_without_ollama(
        self, mock_zhipu, mock_ollama, clean_environment
    ):
        """Test get_default_model works when only Zhipu is available."""
        # Set only ZHIPUAI_API_KEY (no OLLAMA_URL)
        os.environ['ZHIPUAI_API_KEY'] = 'test-key'
        
        # Mock Zhipu provider
        mock_zhipu_instance = MagicMock()
        mock_zhipu_model = MagicMock()
        mock_zhipu_instance.get_default_model.return_value = mock_zhipu_model
        mock_zhipu.return_value = mock_zhipu_instance
        
        # Create ModelManager
        manager = ModelManager()
        
        # Should get Zhipu model since Ollama is not available
        result = manager.get_default_model()
        assert result == mock_zhipu_model
        mock_zhipu_instance.get_default_model.assert_called_once()
        
        # Ollama should not have been initialized
        mock_ollama.assert_not_called()
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_both_providers_work_together(
        self, mock_zhipu, mock_ollama, clean_environment
    ):
        """Test that both providers can be initialized together."""
        # Set both environment variables
        os.environ['OLLAMA_URL'] = 'http://localhost:11434'
        os.environ['ZHIPUAI_API_KEY'] = 'test-key'
        
        # Mock both providers
        mock_ollama_instance = MagicMock()
        mock_zhipu_instance = MagicMock()
        mock_ollama.return_value = mock_ollama_instance
        mock_zhipu.return_value = mock_zhipu_instance
        
        # Create ModelManager
        manager = ModelManager()
        
        # Both providers should be initialized
        mock_ollama.assert_called_once_with('http://localhost:11434')
        mock_zhipu.assert_called_once_with('test-key')
        assert ModelProvider.OLLAMA in manager.providers
        assert ModelProvider.ZHIPU in manager.providers


class TestModelManagerHealthCheck:
    """Test health check functionality with the fix."""
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    @pytest.mark.asyncio
    async def test_health_check_without_ollama(
        self, mock_zhipu, mock_ollama, clean_environment
    ):
        """Test health check when only Zhipu is configured."""
        # Set only ZHIPUAI_API_KEY
        os.environ['ZHIPUAI_API_KEY'] = 'test-key'
        
        # Mock Zhipu provider
        mock_zhipu_instance = MagicMock()
        mock_zhipu_instance.health_check.return_value = {
            "status": "healthy", 
            "provider": "zhipu"
        }
        mock_zhipu.return_value = mock_zhipu_instance
        
        # Create ModelManager
        manager = ModelManager()
        
        # Health check should work with just Zhipu
        health = await manager.health_check()
        
        # Should only have Zhipu health status (no Ollama)
        assert "zhipu" in health
        assert "ollama" not in health
        assert health["zhipu"]["status"] == "healthy"
        
        # Ollama should not have been initialized
        mock_ollama.assert_not_called()


# Marker for easy test selection
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not DEPENDENCIES_AVAILABLE,
        reason="ModelManager dependencies not available"
    )
]