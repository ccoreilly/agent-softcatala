"""
Test suite for the ChatPromptTemplate fix in LangChain agent.

This test ensures that the prompt templates no longer reference {tools} and {tool_names}
variables which are automatically handled by create_openai_tools_agent.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from typing import List, Dict, Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from langchain_agent import LangChainAgent
from telegram_bot import TelegramBot


class TestPromptTemplateFix:
    """Test the prompt template fix for Telegram chat."""
    
    def test_english_prompt_variables(self):
        """Test that English prompt has correct variables."""
        agent = LangChainAgent(tools=[], agent_type="softcatala_english")
        prompt = agent._get_softcatala_english_prompt()
        
        # Check that the prompt is a ChatPromptTemplate
        assert isinstance(prompt, ChatPromptTemplate)
        
        # Check that required variables are present
        expected_variables = {"input", "chat_history", "agent_scratchpad"}
        assert set(prompt.input_variables) == expected_variables
        
        # Check that {tools} and {tool_names} are NOT in input variables
        assert "tools" not in prompt.input_variables
        assert "tool_names" not in prompt.input_variables
        
        # Check that the prompt can be formatted with the expected variables
        try:
            formatted = prompt.format_prompt(
                input="Hello",
                chat_history=[],
                agent_scratchpad=[]
            )
            assert formatted is not None
        except KeyError as e:
            pytest.fail(f"Prompt formatting failed due to missing variable: {e}")
    
    def test_catalan_prompt_variables(self):
        """Test that Catalan prompt has correct variables."""
        agent = LangChainAgent(tools=[], agent_type="softcatala_catalan")
        prompt = agent._get_softcatala_catalan_prompt()
        
        # Check that the prompt is a ChatPromptTemplate
        assert isinstance(prompt, ChatPromptTemplate)
        
        # Check that required variables are present
        expected_variables = {"input", "chat_history", "agent_scratchpad"}
        assert set(prompt.input_variables) == expected_variables
        
        # Check that {tools} and {tool_names} are NOT in input variables
        assert "tools" not in prompt.input_variables
        assert "tool_names" not in prompt.input_variables
        
        # Check that the prompt can be formatted with the expected variables
        try:
            formatted = prompt.format_prompt(
                input="Hola",
                chat_history=[],
                agent_scratchpad=[]
            )
            assert formatted is not None
        except KeyError as e:
            pytest.fail(f"Prompt formatting failed due to missing variable: {e}")
    
    def test_prompt_content_no_variable_references(self):
        """Test that prompt content doesn't contain {tools} or {tool_names} as text."""
        agent = LangChainAgent(tools=[], agent_type="softcatala_english")
        
        # Test English prompt
        english_prompt = agent._get_softcatala_english_prompt()
        english_text = str(english_prompt)
        assert "{tools}" not in english_text
        assert "{tool_names}" not in english_text
        
        # Test Catalan prompt
        agent_catalan = LangChainAgent(tools=[], agent_type="softcatala_catalan")
        catalan_prompt = agent_catalan._get_softcatala_catalan_prompt()
        catalan_text = str(catalan_prompt)
        assert "{tools}" not in catalan_text
        assert "{tool_names}" not in catalan_text
    
    @patch('langchain_agent.ModelManager')
    def test_agent_creation_with_tools(self, mock_model_manager):
        """Test that agent can be created with tools without variable errors."""
        # Mock the model manager and its methods
        mock_model_instance = Mock()
        mock_model_manager.return_value.get_default_model.return_value = mock_model_instance
        mock_model_manager.return_value.get_provider_for_default_model.return_value = Mock()
        
        # Create mock tools with proper structure
        from tools.base import BaseTool, ToolDefinition, ToolParameter
        
        class MockTool(BaseTool):
            def __init__(self):
                super().__init__()
                self._definition = ToolDefinition(
                    name="test_tool",
                    description="A test tool",
                    parameters=[
                        ToolParameter(
                            name="input",
                            type="string",
                            description="Test input parameter",
                            required=True
                        )
                    ]
                )
            
            @property
            def definition(self) -> ToolDefinition:
                return self._definition
            
            async def execute(self, **kwargs):
                return {"result": "test output"}
        
        mock_tool = MockTool()
        
        # Test agent creation should not raise KeyError about missing variables
        try:
            agent = LangChainAgent(tools=[mock_tool], agent_type="softcatala_english")
            assert agent is not None
            assert len(agent.tools) == 1
        except KeyError as e:
            if "tools" in str(e) or "tool_names" in str(e):
                pytest.fail(f"Agent creation failed due to prompt variable error: {e}")
            else:
                # Re-raise if it's a different KeyError
                raise
    
    @patch('langchain_agent.ModelManager')
    def test_agent_creation_without_tools(self, mock_model_manager):
        """Test that agent can be created without tools."""
        # Mock the model manager and its methods
        mock_model_instance = Mock()
        mock_model_manager.return_value.get_default_model.return_value = mock_model_instance
        mock_model_manager.return_value.get_provider_for_default_model.return_value = Mock()
        
        # Test agent creation should not raise KeyError about missing variables
        try:
            agent = LangChainAgent(tools=[], agent_type="softcatala_english")
            assert agent is not None
            assert len(agent.tools) == 0
        except KeyError as e:
            if "tools" in str(e) or "tool_names" in str(e):
                pytest.fail(f"Agent creation failed due to prompt variable error: {e}")
            else:
                # Re-raise if it's a different KeyError
                raise


class TestTelegramChatFunctionality:
    """Test that Telegram chat functionality works with the fixed prompt."""
    
    @patch('langchain_agent.ModelManager')
    @pytest.mark.asyncio
    async def test_chat_stream_no_variable_error(self, mock_model_manager):
        """Test that chat_stream doesn't raise variable errors."""
        # Mock the model manager
        mock_model_instance = Mock()
        mock_model_manager.return_value.get_default_model.return_value = mock_model_instance
        mock_model_manager.return_value.get_provider_for_default_model.return_value = Mock()
        
        # Create agent
        agent = LangChainAgent(tools=[], agent_type="softcatala_english")
        
        # Mock the agent executor to avoid full LLM call
        agent.agent_executor = Mock()
        agent.agent_executor.astream = AsyncMock()
        
        # Mock the stream to return some test data
        async def mock_stream(*args, **kwargs):
            yield {"output": "Test response"}
        
        agent.agent_executor.astream.return_value = mock_stream()
        
        # Test messages that would previously cause the error
        test_messages = [
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        # This should not raise a KeyError about missing 'tools' or 'tool_names' variables
        try:
            response_chunks = []
            async for chunk in agent.chat_stream(test_messages, "test_session"):
                response_chunks.append(chunk)
            
            assert len(response_chunks) > 0
        except KeyError as e:
            if "tools" in str(e) or "tool_names" in str(e):
                pytest.fail(f"chat_stream failed due to prompt variable error: {e}")
            else:
                # Re-raise if it's a different KeyError
                raise
    
    @patch('telegram_bot.Bot')
    @patch('langchain_agent.ModelManager')
    @pytest.mark.asyncio
    async def test_telegram_bot_message_handling(self, mock_model_manager, mock_bot):
        """Test that Telegram bot can handle messages without variable errors."""
        # Mock the model manager
        mock_model_instance = Mock()
        mock_model_manager.return_value.get_default_model.return_value = mock_model_instance
        mock_model_manager.return_value.get_provider_for_default_model.return_value = Mock()
        
        # Create agent and telegram bot
        agent = LangChainAgent(tools=[], agent_type="softcatala_english")
        telegram_bot = TelegramBot("fake_token", agent, max_user_messages=10)
        
        # Mock the agent's chat_stream method
        async def mock_chat_stream(*args, **kwargs):
            yield {"type": "content", "content": "Test response from bot"}
        
        agent.chat_stream = AsyncMock(side_effect=mock_chat_stream)
        
        # Mock Telegram update and context
        mock_update = Mock()
        mock_update.effective_chat.id = 12345
        mock_update.message.text = "Hello bot"
        mock_update.message.reply_text = AsyncMock()
        
        mock_context = Mock()
        mock_context.bot.send_chat_action = AsyncMock()
        
        # This should not raise a KeyError about missing variables
        try:
            await telegram_bot.handle_message(mock_update, mock_context)
            
            # Verify that the message was processed
            assert agent.chat_stream.called
        except KeyError as e:
            if "tools" in str(e) or "tool_names" in str(e):
                pytest.fail(f"Telegram message handling failed due to prompt variable error: {e}")
            else:
                # Re-raise if it's a different KeyError
                raise


class TestBackwardCompatibility:
    """Test that the fix doesn't break existing functionality."""
    
    @patch('langchain_agent.ModelManager')
    def test_both_agent_types_work(self, mock_model_manager):
        """Test that both English and Catalan agent types work."""
        mock_model_instance = Mock()
        mock_model_manager.return_value.get_default_model.return_value = mock_model_instance
        mock_model_manager.return_value.get_provider_for_default_model.return_value = Mock()
        
        # Test English agent
        english_agent = LangChainAgent(tools=[], agent_type="softcatala_english")
        assert english_agent.agent_type == "softcatala_english"
        
        # Test Catalan agent
        catalan_agent = LangChainAgent(tools=[], agent_type="softcatala_catalan")
        assert catalan_agent.agent_type == "softcatala_catalan"
        
        # Test default (should be English)
        default_agent = LangChainAgent(tools=[], agent_type="unknown_type")
        assert default_agent.agent_type == "unknown_type"
        # Should use English prompt as fallback
        english_prompt = english_agent._get_softcatala_english_prompt()
        default_prompt = default_agent._get_softcatala_english_prompt()
        assert str(english_prompt) == str(default_prompt)
    
    @patch('langchain_agent.ModelManager')
    def test_tool_integration_still_works(self, mock_model_manager):
        """Test that tools are still properly integrated despite prompt changes."""
        mock_model_instance = Mock()
        mock_model_manager.return_value.get_default_model.return_value = mock_model_instance
        mock_model_manager.return_value.get_provider_for_default_model.return_value = Mock()
        
        # Create mock tool with proper structure
        from tools.base import BaseTool, ToolDefinition, ToolParameter
        
        class MockSearchTool(BaseTool):
            def __init__(self):
                super().__init__()
                self._definition = ToolDefinition(
                    name="search_tool",
                    description="A search tool",
                    parameters=[
                        ToolParameter(
                            name="query",
                            type="string",
                            description="Search query",
                            required=True
                        )
                    ]
                )
            
            @property
            def definition(self) -> ToolDefinition:
                return self._definition
            
            async def execute(self, **kwargs):
                return {"result": "search results"}
        
        mock_tool = MockSearchTool()
        
        # Create agent with tools
        agent = LangChainAgent(tools=[mock_tool], agent_type="softcatala_english")
        
        # Verify tools are properly wrapped and stored
        assert len(agent.tools) == 1
        assert agent.tools[0].name == "search_tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])