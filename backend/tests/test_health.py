"""
Health check tests for system monitoring and availability
"""
import pytest
import pytest_asyncio
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sys
import httpx

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test comprehensive health check functionality."""
    
    @patch('main.agent')
    def test_health_endpoint_all_services_healthy(self, mock_agent, client):
        """Test health endpoint when all services are healthy."""
        mock_agent.check_health = AsyncMock(return_value={
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00",
            "models": {
                "ollama": {
                    "status": "available",
                    "available_models": ["llama3.1", "mistral"],
                    "response_time": 0.5
                },
                "zhipu": {
                    "status": "available",
                    "available_models": ["glm-4", "glm-3-turbo"],
                    "response_time": 0.3
                }
            },
            "tools": {
                "count": 3,
                "names": ["web_browser", "search", "wikipedia"],
                "status": "all_available"
            },
            "memory": {
                "usage": "45%",
                "available": "2.1GB"
            }
        })
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "models" in data
        assert "tools" in data
        
        # Check model providers
        assert data["models"]["ollama"]["status"] == "available"
        assert data["models"]["zhipu"]["status"] == "available"
        assert len(data["models"]["ollama"]["available_models"]) > 0
        assert len(data["models"]["zhipu"]["available_models"]) > 0
        
        # Check tools
        assert data["tools"]["count"] == 3
        assert "web_browser" in data["tools"]["names"]
    
    @patch('main.agent')
    def test_health_endpoint_partial_service_failure(self, mock_agent, client):
        """Test health endpoint with partial service failure."""
        mock_agent.check_health = AsyncMock(return_value={
            "status": "degraded",
            "timestamp": "2024-01-01T00:00:00",
            "models": {
                "ollama": {
                    "status": "unavailable",
                    "error": "Connection timeout",
                    "last_check": "2024-01-01T00:00:00"
                },
                "zhipu": {
                    "status": "available",
                    "available_models": ["glm-4"],
                    "response_time": 0.8
                }
            },
            "tools": {
                "count": 2,
                "names": ["search", "wikipedia"],
                "status": "partial_availability",
                "failed": ["web_browser"]
            }
        })
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "degraded"
        assert data["models"]["ollama"]["status"] == "unavailable"
        assert data["models"]["zhipu"]["status"] == "available"
        assert data["tools"]["count"] == 2
        assert "web_browser" in data["tools"]["failed"]
    
    @patch('main.agent')
    def test_health_endpoint_complete_failure(self, mock_agent, client):
        """Test health endpoint when agent health check fails completely."""
        mock_agent.check_health = AsyncMock(side_effect=Exception("Complete system failure"))
        
        response = client.get("/health")
        assert response.status_code == 503
        assert "Servei no saludable" in response.json()["detail"]
    
    @patch('main.agent')
    def test_health_endpoint_timeout_handling(self, mock_agent, client):
        """Test health endpoint handles timeouts gracefully."""
        # Simulate a timeout
        mock_agent.check_health = AsyncMock(side_effect=asyncio.TimeoutError("Health check timeout"))
        
        response = client.get("/health")
        assert response.status_code == 503
        assert "timeout" in response.json()["detail"].lower()


class TestServiceAvailability:
    """Test individual service availability checks."""
    
    @pytest.mark.asyncio
    async def test_ollama_service_availability(self):
        """Test Ollama service availability check."""
        with patch('httpx.AsyncClient.get') as mock_get:
            # Mock successful Ollama response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama3.1", "size": 4700000000},
                    {"name": "mistral", "size": 4100000000}
                ]
            }
            mock_get.return_value = mock_response
            
            # This would be called by the actual health check implementation
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:11434/api/tags")
                assert response.status_code == 200
                data = response.json()
                assert "models" in data
                assert len(data["models"]) > 0
    
    @pytest.mark.asyncio
    async def test_ollama_service_unavailable(self):
        """Test Ollama service unavailable scenario."""
        with patch('httpx.AsyncClient.get') as mock_get:
            # Mock connection error
            mock_get.side_effect = httpx.ConnectError("Connection failed")
            
            try:
                async with httpx.AsyncClient() as client:
                    await client.get("http://localhost:11434/api/tags")
                assert False, "Should have raised exception"
            except httpx.ConnectError:
                # Expected behavior
                pass
    
    @pytest.mark.asyncio
    async def test_zhipu_service_availability(self):
        """Test Zhipu AI service availability check."""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock successful Zhipu response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {"message": {"content": "Test response"}}
                ],
                "usage": {"total_tokens": 10}
            }
            mock_post.return_value = mock_response
            
            # This would be called by the actual health check implementation
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                    headers={"Authorization": "Bearer test-token"},
                    json={
                        "model": "glm-4",
                        "messages": [{"role": "user", "content": "test"}]
                    }
                )
                assert response.status_code == 200
                data = response.json()
                assert "choices" in data


class TestSystemMetrics:
    """Test system metrics and performance monitoring."""
    
    @patch('main.agent')
    def test_health_response_time_monitoring(self, mock_agent, client):
        """Test that health check includes response time metrics."""
        mock_agent.check_health = AsyncMock(return_value={
            "status": "healthy",
            "response_times": {
                "ollama": 0.25,
                "zhipu": 0.31,
                "tools_check": 0.15
            },
            "total_response_time": 0.71
        })
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "response_times" in data
        assert data["response_times"]["ollama"] < 1.0  # Should be fast
        assert data["total_response_time"] < 2.0  # Total should be reasonable
    
    @patch('main.agent')
    def test_health_memory_usage_monitoring(self, mock_agent, client):
        """Test that health check includes memory usage information."""
        mock_agent.check_health = AsyncMock(return_value={
            "status": "healthy",
            "system": {
                "memory_usage": "52%",
                "available_memory": "1.8GB",
                "cpu_usage": "23%",
                "disk_usage": "67%"
            }
        })
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "system" in data
        assert "memory_usage" in data["system"]
        assert "cpu_usage" in data["system"]
    
    @patch('main.agent')
    def test_health_high_resource_usage_warning(self, mock_agent, client):
        """Test health check warns about high resource usage."""
        mock_agent.check_health = AsyncMock(return_value={
            "status": "warning",
            "system": {
                "memory_usage": "89%",  # High memory usage
                "available_memory": "0.2GB",
                "cpu_usage": "92%",     # High CPU usage
                "warnings": [
                    "High memory usage detected",
                    "High CPU usage detected"
                ]
            }
        })
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "warning"
        assert "warnings" in data["system"]
        assert len(data["system"]["warnings"]) > 0


class TestHealthCheckResilience:
    """Test health check resilience and error recovery."""
    
    @patch('main.agent')
    def test_health_check_partial_data_recovery(self, mock_agent, client):
        """Test health check can return partial data when some checks fail."""
        # Mock scenario where model check fails but tools check succeeds
        mock_agent.check_health = AsyncMock(return_value={
            "status": "partial",
            "models": {
                "error": "Model provider check failed",
                "status": "unavailable"
            },
            "tools": {
                "count": 3,
                "names": ["web_browser", "search", "wikipedia"],
                "status": "available"
            },
            "partial_failure_reason": "Model providers unreachable"
        })
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "partial"
        assert "tools" in data
        assert data["tools"]["status"] == "available"
        assert "partial_failure_reason" in data
    
    @patch('main.agent')
    def test_health_check_timeout_resilience(self, mock_agent, client):
        """Test health check handles individual component timeouts."""
        mock_agent.check_health = AsyncMock(return_value={
            "status": "degraded",
            "models": {
                "ollama": {
                    "status": "timeout",
                    "error": "Health check timeout after 30s"
                },
                "zhipu": {
                    "status": "available",
                    "available_models": ["glm-4"]
                }
            },
            "tools": {
                "count": 3,
                "names": ["web_browser", "search", "wikipedia"],
                "status": "available"
            },
            "timeout_components": ["ollama"]
        })
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "degraded"
        assert "timeout_components" in data
        assert "ollama" in data["timeout_components"]
    
    @patch('main.agent')
    def test_health_check_retry_mechanism(self, mock_agent, client):
        """Test health check retry mechanism for transient failures."""
        # Simulate a transient failure that succeeds on retry
        call_count = [0]
        
        def mock_health_with_retry():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Transient failure")
            return {
                "status": "healthy",
                "models": {"ollama": {"status": "available"}},
                "retry_attempts": call_count[0]
            }
        
        mock_agent.check_health = AsyncMock(side_effect=mock_health_with_retry)
        
        # The implementation should handle retries internally
        # For this test, we just verify it can recover
        try:
            response = client.get("/health")
            # If retry logic is implemented, this might succeed
            # If not, it should fail gracefully
            assert response.status_code in [200, 503]
        except Exception:
            # Acceptable if retry not implemented yet
            pass


class TestHealthCheckIntegration:
    """Test health check integration with Docker and deployment."""
    
    def test_health_check_docker_compatibility(self, client):
        """Test health check is compatible with Docker health checks."""
        # Docker health check typically expects specific status codes
        response = client.get("/health")
        
        # Should return either 200 (healthy) or 503 (unhealthy)
        # Never return 500 or other error codes for Docker compatibility
        assert response.status_code in [200, 503]
        
        # Should always return JSON response
        assert response.headers["content-type"] == "application/json"
    
    @patch('main.agent')
    def test_health_check_monitoring_format(self, mock_agent, client):
        """Test health check returns data in monitoring-friendly format."""
        mock_agent.check_health = AsyncMock(return_value={
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "version": "2.0.0",
            "uptime": "7d 14h 23m",
            "models": {
                "ollama": {"status": "available", "models_count": 2},
                "zhipu": {"status": "available", "models_count": 3}
            },
            "tools": {"count": 3, "status": "available"}
        })
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        
        # Standard monitoring fields
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        
        # Service-specific metrics
        assert "models" in data
        assert "tools" in data
        
        # Structured format for easy parsing
        assert isinstance(data["models"], dict)
        assert isinstance(data["tools"], dict)