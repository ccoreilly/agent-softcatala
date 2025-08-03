"""
Unit tests for ModelManager class, specifically testing the Ollama initialization fix.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
import logging

# Import the classes we want to test
try:
    from models.model_manager import ModelManager, ModelProvider
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE,
    reason="ModelManager dependencies not available"
)


class TestModelManagerInitialization:
    """Test ModelManager provider initialization logic."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing environment variables that might affect tests
        env_vars_to_clear = ['OLLAMA_URL', 'ZHIPUAI_API_KEY']
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_ollama_not_initialized_when_url_not_set(self, mock_zhipu, mock_ollama):
        """Test that Ollama is not initialized when OLLAMA_URL is not set."""
        # Ensure OLLAMA_URL is not set
        assert 'OLLAMA_URL' not in os.environ
        
        # Create ModelManager
        manager = ModelManager()
        
        # Ollama should not be initialized
        mock_ollama.assert_not_called()
        assert ModelProvider.OLLAMA not in manager.providers
        
        # Zhipu should also not be initialized (no API key)
        mock_zhipu.assert_not_called()
        assert ModelProvider.ZHIPU not in manager.providers
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_ollama_not_initialized_when_url_empty(self, mock_zhipu, mock_ollama):
        """Test that Ollama is not initialized when OLLAMA_URL is empty."""
        # Set OLLAMA_URL to empty string
        os.environ['OLLAMA_URL'] = ''
        
        # Create ModelManager
        manager = ModelManager()
        
        # Ollama should not be initialized
        mock_ollama.assert_not_called()
        assert ModelProvider.OLLAMA not in manager.providers
        
        # Zhipu should also not be initialized (no API key)
        mock_zhipu.assert_not_called()
        assert ModelProvider.ZHIPU not in manager.providers
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_ollama_not_initialized_when_url_whitespace_only(self, mock_zhipu, mock_ollama):
        """Test that Ollama is not initialized when OLLAMA_URL is only whitespace."""
        # Set OLLAMA_URL to whitespace only
        os.environ['OLLAMA_URL'] = '   \t\n  '
        
        # Create ModelManager
        manager = ModelManager()
        
        # Ollama should not be initialized
        mock_ollama.assert_not_called()
        assert ModelProvider.OLLAMA not in manager.providers
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_ollama_initialized_when_url_set(self, mock_zhipu, mock_ollama):
        """Test that Ollama is initialized when OLLAMA_URL is properly set."""
        # Set OLLAMA_URL
        test_url = 'http://localhost:11434'
        os.environ['OLLAMA_URL'] = test_url
        
        # Mock the provider instances
        mock_ollama_instance = MagicMock()
        mock_ollama.return_value = mock_ollama_instance
        
        # Create ModelManager
        manager = ModelManager()
        
        # Ollama should be initialized with the correct URL
        mock_ollama.assert_called_once_with(test_url)
        assert ModelProvider.OLLAMA in manager.providers
        assert manager.providers[ModelProvider.OLLAMA] == mock_ollama_instance
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_zhipu_initialized_when_api_key_set(self, mock_zhipu, mock_ollama):
        """Test that Zhipu is initialized when ZHIPUAI_API_KEY is set."""
        # Set ZHIPUAI_API_KEY
        test_key = 'test-zhipu-key'
        os.environ['ZHIPUAI_API_KEY'] = test_key
        
        # Mock the provider instances
        mock_zhipu_instance = MagicMock()
        mock_zhipu.return_value = mock_zhipu_instance
        
        # Create ModelManager
        manager = ModelManager()
        
        # Zhipu should be initialized with the correct API key
        mock_zhipu.assert_called_once_with(test_key)
        assert ModelProvider.ZHIPU in manager.providers
        assert manager.providers[ModelProvider.ZHIPU] == mock_zhipu_instance
        
        # Ollama should not be initialized (no URL)
        mock_ollama.assert_not_called()
        assert ModelProvider.OLLAMA not in manager.providers
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_both_providers_initialized_when_both_configured(self, mock_zhipu, mock_ollama):
        """Test that both providers are initialized when both are configured."""
        # Set both environment variables
        test_url = 'http://localhost:11434'
        test_key = 'test-zhipu-key'
        os.environ['OLLAMA_URL'] = test_url
        os.environ['ZHIPUAI_API_KEY'] = test_key
        
        # Mock the provider instances
        mock_ollama_instance = MagicMock()
        mock_zhipu_instance = MagicMock()
        mock_ollama.return_value = mock_ollama_instance
        mock_zhipu.return_value = mock_zhipu_instance
        
        # Create ModelManager
        manager = ModelManager()
        
        # Both providers should be initialized
        mock_ollama.assert_called_once_with(test_url)
        mock_zhipu.assert_called_once_with(test_key)
        assert ModelProvider.OLLAMA in manager.providers
        assert ModelProvider.ZHIPU in manager.providers
        assert manager.providers[ModelProvider.OLLAMA] == mock_ollama_instance
        assert manager.providers[ModelProvider.ZHIPU] == mock_zhipu_instance


class TestModelManagerErrorHandling:
    """Test ModelManager error handling during provider initialization."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing environment variables that might affect tests
        env_vars_to_clear = ['OLLAMA_URL', 'ZHIPUAI_API_KEY']
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_ollama_initialization_error_handled(self, mock_zhipu, mock_ollama, caplog):
        """Test that Ollama initialization errors are handled gracefully."""
        # Set OLLAMA_URL
        os.environ['OLLAMA_URL'] = 'http://localhost:11434'
        
        # Make OllamaProvider raise an exception
        mock_ollama.side_effect = Exception("Connection failed")
        
        # Create ModelManager
        with caplog.at_level(logging.WARNING):
            manager = ModelManager()
        
        # Ollama should be attempted but fail gracefully
        mock_ollama.assert_called_once()
        assert ModelProvider.OLLAMA not in manager.providers
        
        # Check that warning was logged
        assert "Failed to initialize Ollama provider" in caplog.text
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_zhipu_initialization_error_handled(self, mock_zhipu, mock_ollama, caplog):
        """Test that Zhipu initialization errors are handled gracefully."""
        # Set ZHIPUAI_API_KEY
        os.environ['ZHIPUAI_API_KEY'] = 'test-key'
        
        # Make ZhipuProvider raise an exception
        mock_zhipu.side_effect = Exception("API key invalid")
        
        # Create ModelManager
        with caplog.at_level(logging.WARNING):
            manager = ModelManager()
        
        # Zhipu should be attempted but fail gracefully
        mock_zhipu.assert_called_once()
        assert ModelProvider.ZHIPU not in manager.providers
        
        # Check that warning was logged
        assert "Failed to initialize Zhipu AI provider" in caplog.text


class TestModelManagerLogging:
    """Test ModelManager logging behavior."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing environment variables that might affect tests
        env_vars_to_clear = ['OLLAMA_URL', 'ZHIPUAI_API_KEY']
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_ollama_not_found_warning_logged(self, mock_zhipu, mock_ollama, caplog):
        """Test that appropriate warning is logged when OLLAMA_URL is not set."""
        # Ensure OLLAMA_URL is not set
        assert 'OLLAMA_URL' not in os.environ
        
        # Create ModelManager
        with caplog.at_level(logging.WARNING):
            manager = ModelManager()
        
        # Check that warning was logged
        assert "OLLAMA_URL not found or empty, Ollama provider not initialized" in caplog.text
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_zhipu_not_found_warning_logged(self, mock_zhipu, mock_ollama, caplog):
        """Test that appropriate warning is logged when ZHIPUAI_API_KEY is not set."""
        # Ensure ZHIPUAI_API_KEY is not set
        assert 'ZHIPUAI_API_KEY' not in os.environ
        
        # Create ModelManager
        with caplog.at_level(logging.WARNING):
            manager = ModelManager()
        
        # Check that warning was logged
        assert "ZHIPUAI_API_KEY not found, Zhipu AI provider not initialized" in caplog.text
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_ollama_initialized_info_logged(self, mock_zhipu, mock_ollama, caplog):
        """Test that appropriate info is logged when Ollama is initialized."""
        # Set OLLAMA_URL
        test_url = 'http://localhost:11434'
        os.environ['OLLAMA_URL'] = test_url
        
        # Mock the provider
        mock_ollama.return_value = MagicMock()
        
        # Create ModelManager
        with caplog.at_level(logging.INFO):
            manager = ModelManager()
        
        # Check that info was logged
        assert f"Initialized Ollama provider at {test_url}" in caplog.text
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_zhipu_initialized_info_logged(self, mock_zhipu, mock_ollama, caplog):
        """Test that appropriate info is logged when Zhipu is initialized."""
        # Set ZHIPUAI_API_KEY
        os.environ['ZHIPUAI_API_KEY'] = 'test-key'
        
        # Mock the provider
        mock_zhipu.return_value = MagicMock()
        
        # Create ModelManager
        with caplog.at_level(logging.INFO):
            manager = ModelManager()
        
        # Check that info was logged
        assert "Initialized Zhipu AI provider" in caplog.text


class TestModelManagerGetDefaultModel:
    """Test ModelManager get_default_model behavior with different provider configurations."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing environment variables that might affect tests
        env_vars_to_clear = ['OLLAMA_URL', 'ZHIPUAI_API_KEY']
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_get_default_model_with_only_zhipu(self, mock_zhipu, mock_ollama):
        """Test get_default_model when only Zhipu is available."""
        # Set only ZHIPUAI_API_KEY
        os.environ['ZHIPUAI_API_KEY'] = 'test-key'
        
        # Mock providers
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
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_get_default_model_prefers_ollama_when_available(self, mock_zhipu, mock_ollama):
        """Test get_default_model prefers Ollama when both providers are available."""
        # Set both environment variables
        os.environ['OLLAMA_URL'] = 'http://localhost:11434'
        os.environ['ZHIPUAI_API_KEY'] = 'test-key'
        
        # Mock providers
        mock_ollama_instance = MagicMock()
        mock_ollama_model = MagicMock()
        mock_ollama_instance.get_default_model.return_value = mock_ollama_model
        mock_ollama.return_value = mock_ollama_instance
        
        mock_zhipu_instance = MagicMock()
        mock_zhipu.return_value = mock_zhipu_instance
        
        # Create ModelManager
        manager = ModelManager()
        
        # Should get Ollama model (preferred)
        result = manager.get_default_model()
        assert result == mock_ollama_model
        mock_ollama_instance.get_default_model.assert_called_once()
        # Zhipu should not be called since Ollama is preferred
        mock_zhipu_instance.get_default_model.assert_not_called()
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_get_default_model_falls_back_to_zhipu_when_ollama_fails(self, mock_zhipu, mock_ollama):
        """Test get_default_model falls back to Zhipu when Ollama fails."""
        # Set both environment variables
        os.environ['OLLAMA_URL'] = 'http://localhost:11434'
        os.environ['ZHIPUAI_API_KEY'] = 'test-key'
        
        # Mock providers
        mock_ollama_instance = MagicMock()
        mock_ollama_instance.get_default_model.side_effect = Exception("Ollama connection failed")
        mock_ollama.return_value = mock_ollama_instance
        
        mock_zhipu_instance = MagicMock()
        mock_zhipu_model = MagicMock()
        mock_zhipu_instance.get_default_model.return_value = mock_zhipu_model
        mock_zhipu.return_value = mock_zhipu_instance
        
        # Create ModelManager
        manager = ModelManager()
        
        # Should fall back to Zhipu model
        result = manager.get_default_model()
        assert result == mock_zhipu_model
        mock_ollama_instance.get_default_model.assert_called_once()
        mock_zhipu_instance.get_default_model.assert_called_once()
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_get_default_model_raises_when_no_providers_available(self, mock_zhipu, mock_ollama):
        """Test get_default_model raises RuntimeError when no providers are available."""
        # Don't set any environment variables
        assert 'OLLAMA_URL' not in os.environ
        assert 'ZHIPUAI_API_KEY' not in os.environ
        
        # Create ModelManager (no providers will be initialized)
        manager = ModelManager()
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="No available language models found"):
            manager.get_default_model()


class TestModelManagerRegression:
    """Regression tests for the Ollama initialization fix."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing environment variables that might affect tests
        env_vars_to_clear = ['OLLAMA_URL', 'ZHIPUAI_API_KEY']
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
    
    @patch('models.model_manager.OllamaProvider')
    @patch('models.model_manager.ZhipuProvider')
    def test_regression_ollama_not_initialized_without_url(self, mock_zhipu, mock_ollama):
        """
        Regression test: Ensure Ollama is not initialized when OLLAMA_URL is not set.
        
        This test specifically addresses the original issue where Ollama was always
        initialized with a default URL even when the environment variable was not set.
        """
        # This is the exact scenario from the bug report:
        # - OLLAMA_URL is not set
        # - Only ZHIPUAI_API_KEY is configured
        os.environ['ZHIPUAI_API_KEY'] = 'test-key'
        
        # Mock Zhipu provider
        mock_zhipu.return_value = MagicMock()
        
        # Create ModelManager
        manager = ModelManager()
        
        # CRITICAL: Ollama should NOT be initialized
        mock_ollama.assert_not_called()
        assert ModelProvider.OLLAMA not in manager.providers
        
        # Only Zhipu should be initialized
        mock_zhipu.assert_called_once_with('test-key')
        assert ModelProvider.ZHIPU in manager.providers
        
        # This should NOT produce any Ollama connection errors in logs
        # (which was the original problem)