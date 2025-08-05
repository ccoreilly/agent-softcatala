#!/usr/bin/env python3
"""
Integration tests for tool execution with real API calls.
These tests can run in CI with ZHIPUAI_API_KEY environment variable.
"""

import asyncio
import os
import pytest
import logging
from unittest.mock import patch

from langchain_agent import LangChainAgent
from tools.catalan_synonyms import CatalanSynonymsTool
from tools.catalan_spell_checker import CatalanSpellCheckerTool
from tools.langchain_tools import LangChainToolWrapper

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestToolExecutionIntegration:
    """Integration tests for tool execution with real API calls."""

    def test_tool_schema_generation(self):
        """Test that tool schemas are properly generated."""
        # Test Catalan synonyms tool
        synonyms_tool = CatalanSynonymsTool()
        wrapped_tool = LangChainToolWrapper(synonyms_tool)
        
        assert wrapped_tool.args_schema is not None
        assert hasattr(wrapped_tool.args_schema, '__fields__')
        
        # Check that required fields are present
        schema_instance = wrapped_tool.args_schema(action="search", word="test")
        assert schema_instance.action == "search"
        assert schema_instance.word == "test"

    @pytest.mark.asyncio
    async def test_direct_tool_execution(self):
        """Test direct tool execution without agent."""
        synonyms_tool = CatalanSynonymsTool()
        
        # Test successful API call
        result = await synonyms_tool.execute(action="search", word="hola")
        
        assert result is not None
        assert isinstance(result, dict)
        assert result.get("status") == "success"
        assert "word" in result
        assert result["word"] == "hola"

    @pytest.mark.asyncio
    async def test_langchain_wrapper_execution(self):
        """Test LangChain tool wrapper execution."""
        synonyms_tool = CatalanSynonymsTool()
        wrapped_tool = LangChainToolWrapper(synonyms_tool)
        
        # Test wrapper execution
        result = await wrapped_tool._arun(action="search", word="hola")
        
        assert result is not None
        assert isinstance(result, dict)
        assert result.get("status") == "success"
        assert "word" in result

    @patch.dict(os.environ, {"OLLAMA_URL": "http://localhost:11434"}, clear=False)
    def test_agent_initialization_with_tools(self):
        """Test that agent initializes correctly with tools."""
        from models.model_manager import ModelManager
        from unittest.mock import MagicMock
        
        synonyms_tool = CatalanSynonymsTool()
        spell_checker_tool = CatalanSpellCheckerTool()
        
        # Mock the model manager to avoid requiring actual models
        with patch.object(ModelManager, 'get_default_model') as mock_get_model:
            mock_llm = MagicMock()
            mock_llm.bind_tools = MagicMock(return_value=mock_llm)
            mock_get_model.return_value = mock_llm
            
            # Initialize agent with tools
            agent = LangChainAgent(
                tools=[synonyms_tool, spell_checker_tool], 
                agent_type="softcatala_english"
            )
            
            assert agent is not None
            assert len(agent.tools) == 2
            assert all(tool.args_schema is not None for tool in agent.tools)

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OLLAMA_URL": "http://localhost:11434"}, clear=False)
    async def test_agent_health_check(self):
        """Test agent health check with tools."""
        from models.model_manager import ModelManager
        from unittest.mock import MagicMock
        
        synonyms_tool = CatalanSynonymsTool()
        spell_checker_tool = CatalanSpellCheckerTool()
        
        # Mock the model manager to avoid requiring actual models
        with patch.object(ModelManager, 'get_default_model') as mock_get_model:
            with patch.object(ModelManager, 'health_check') as mock_health_check:
                mock_llm = MagicMock()
                mock_llm.bind_tools = MagicMock(return_value=mock_llm)
                mock_get_model.return_value = mock_llm
                mock_health_check.return_value = {"ollama": {"status": "healthy"}}
                
                agent = LangChainAgent(
                    tools=[synonyms_tool, spell_checker_tool], 
                    agent_type="softcatala_english"
                )
                
                health = await agent.check_health()
                
                assert health is not None
                assert health["agent"] == "healthy"
                assert health["tools"]["count"] == 2
                assert "catalan_synonyms" in health["tools"]["names"]
                assert "catalan_spell_checker" in health["tools"]["names"]

    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("ZHIPUAI_API_KEY"), reason="ZHIPUAI_API_KEY not set")
    async def test_agent_streaming_with_zhipu(self):
        """Test agent streaming with Zhipu provider and tool usage."""
        synonyms_tool = CatalanSynonymsTool()
        spell_checker_tool = CatalanSpellCheckerTool()
        
        # Remove Ollama URL to force Zhipu provider
        with patch.dict(os.environ, {}, clear=True):
            os.environ["ZHIPUAI_API_KEY"] = os.getenv("ZHIPUAI_API_KEY")
            
            agent = LangChainAgent(
                tools=[synonyms_tool, spell_checker_tool], 
                agent_type="softcatala_english"
            )
            
            # Switch to Zhipu provider
            agent.switch_model("zhipu", "glm-4-flash")
            
            # Test message that should trigger tool usage
            test_messages = [
                {
                    "role": "user",
                    "content": "Necessito sinònims per a la paraula 'casa'. Pots utilitzar l'eina de sinònims per ajudar-me?"
                }
            ]
            
            chunks_received = []
            tool_calls_found = []
            tool_results_found = []
            
            async for chunk in agent.chat_stream(test_messages, "test_session"):
                chunks_received.append(chunk)
                logger.info(f"Received chunk: {chunk}")
                
                if chunk.get("type") == "tool_call":
                    tool_calls_found.append(chunk)
                elif chunk.get("type") == "tool_result":
                    tool_results_found.append(chunk)
            
            # Assertions
            assert len(chunks_received) > 0, "No chunks received from agent"
            logger.info(f"Total chunks: {len(chunks_received)}, Tool calls: {len(tool_calls_found)}, Tool results: {len(tool_results_found)}")
            
            # We should have at least some meaningful response
            content_chunks = [c for c in chunks_received if c.get("type") == "content"]
            assert len(content_chunks) > 0, "No content chunks received"

    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("ZHIPUAI_API_KEY"), reason="ZHIPUAI_API_KEY not set")
    async def test_simple_zhipu_response(self):
        """Test basic response generation with Zhipu provider."""
        # Remove Ollama URL to force Zhipu provider
        with patch.dict(os.environ, {}, clear=True):
            os.environ["ZHIPUAI_API_KEY"] = os.getenv("ZHIPUAI_API_KEY")
            
            # Initialize agent without tools first
            agent = LangChainAgent(tools=[], agent_type="softcatala_english")
            
            # Switch to Zhipu provider
            agent.switch_model("zhipu", "glm-4-flash")
            
            test_messages = [
                {
                    "role": "user",
                    "content": "Hola! Com estàs?"
                }
            ]
            
            response_chunks = []
            async for chunk in agent.chat_stream(test_messages, "test_session"):
                response_chunks.append(chunk)
                logger.info(f"Received chunk: {chunk}")
            
            assert len(response_chunks) > 0, "No response chunks received"
            
            # Should have content chunks
            content_chunks = [c for c in response_chunks if c.get("type") == "content"]
            assert len(content_chunks) > 0, "No content in response"

    def test_tool_parameter_validation(self):
        """Test tool parameter validation."""
        synonyms_tool = CatalanSynonymsTool()
        
        # Test valid parameters
        try:
            synonyms_tool.validate_parameters({"action": "search", "word": "test"})
        except Exception as e:
            pytest.fail(f"Valid parameters should not raise exception: {e}")
        
        # Test missing required parameter
        with pytest.raises(ValueError, match="Required parameter 'action' missing"):
            synonyms_tool.validate_parameters({"word": "test"})
        
        with pytest.raises(ValueError, match="Required parameter 'word' missing"):
            synonyms_tool.validate_parameters({"action": "search"})

    def test_multiple_tool_types(self):
        """Test that different tool types work correctly."""
        synonyms_tool = CatalanSynonymsTool()
        spell_checker_tool = CatalanSpellCheckerTool()
        
        # Test both tools have proper definitions
        assert synonyms_tool.definition.name == "catalan_synonyms"
        assert spell_checker_tool.definition.name == "catalan_spell_checker"
        
        # Test both tools have parameters
        assert len(synonyms_tool.definition.parameters) > 0
        assert len(spell_checker_tool.definition.parameters) > 0
        
        # Test wrapped tools have schemas
        wrapped_synonyms = LangChainToolWrapper(synonyms_tool)
        wrapped_spell_checker = LangChainToolWrapper(spell_checker_tool)
        
        assert wrapped_synonyms.args_schema is not None
        assert wrapped_spell_checker.args_schema is not None


# Helper functions for CI
def run_integration_tests():
    """Run integration tests programmatically."""
    import sys
    
    # Run pytest programmatically
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])
    
    return exit_code == 0


if __name__ == "__main__":
    # Can be run directly for debugging
    success = run_integration_tests()
    exit(0 if success else 1)