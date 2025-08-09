"""
Test for Telegram bot debug mode functionality.

This test verifies that tool output (tool_call, tool_result, tool_error) 
is only shown when debug mode is enabled.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from telegram_bot import TelegramBot
from langchain_agent import LangChainAgent


class TestTelegramDebugMode:
    """Test class for Telegram bot debug mode functionality."""
    
    @patch('telegram_bot.Bot')
    @patch('langchain_agent.ModelManager')
    @pytest.mark.asyncio
    async def test_debug_mode_enabled_shows_tool_output(self, mock_model_manager, mock_bot):
        """Test that tool output is shown when debug mode is enabled."""
        # Mock the model manager
        mock_model_instance = Mock()
        mock_model_manager.return_value.get_default_model.return_value = mock_model_instance
        
        # Create telegram bot (agent is created per-message now)
        telegram_bot = TelegramBot("fake_token", "softcatala_english", max_user_messages=10)
        
        # Enable debug mode for test chat
        chat_id = "12345"
        telegram_bot.debug_mode[chat_id] = True
        
        # Mock the agent's chat_stream method to return tool events
        async def mock_chat_stream(*args, **kwargs):
            yield {"type": "tool_call", "tool": "test_tool", "input": {"param": "value"}, "timestamp": "2023-01-01 12:00:00"}
            yield {"type": "tool_result", "tool": "test_tool", "result": {"status": "success"}, "input": {"param": "value"}, "timestamp": "2023-01-01 12:00:01"}
            yield {"type": "tool_error", "tool": "test_tool", "error": "Test error", "timestamp": "2023-01-01 12:00:02"}
            yield {"type": "content", "content": "Final response"}
        
        # Mock the _create_agent_for_user method to return an agent with our mock chat_stream
        def mock_create_agent_for_user(chat_id):
            mock_agent = Mock()
            mock_agent.chat_stream = mock_chat_stream
            return mock_agent
        telegram_bot._create_agent_for_user = mock_create_agent_for_user
        
        # Mock Telegram update and context
        mock_update = Mock()
        mock_update.effective_chat.id = int(chat_id)
        mock_update.message.text = "Hello bot"
        mock_reply_msg = Mock()
        mock_reply_msg.chat_id = int(chat_id)
        mock_reply_msg.message_id = 123
        mock_reply_msg.edit_text = AsyncMock()
        mock_update.message.reply_text = AsyncMock(return_value=mock_reply_msg)
        
        mock_context = Mock()
        mock_context.bot.send_chat_action = AsyncMock()
        
        # Track all edit calls
        edit_calls = []
        async def track_edit_calls(text, **kwargs):
            edit_calls.append(text)
        mock_reply_msg.edit_text.side_effect = track_edit_calls
        
        # Process the message
        await telegram_bot.handle_message(mock_update, mock_context)
        
        # Verify that tool output was shown (debug mode enabled)
        edit_texts = [call for call in edit_calls]
        
        # Should have tool call message
        tool_call_found = any("🔧 **Eina seleccionada:**" in text for text in edit_texts)
        assert tool_call_found, f"Tool call message not found in debug mode. Edit calls: {edit_texts}"
        
        # Should have tool result message  
        tool_result_found = any("✅ **Eina completada:**" in text for text in edit_texts)
        assert tool_result_found, f"Tool result message not found in debug mode. Edit calls: {edit_texts}"
        
        # Should have tool error message
        tool_error_found = any("❌ **Error d'eina:**" in text for text in edit_texts)
        assert tool_error_found, f"Tool error message not found in debug mode. Edit calls: {edit_texts}"
        
        # Should have final response
        final_response_found = any("🤖 Final response" in text for text in edit_texts)
        assert final_response_found, f"Final response not found. Edit calls: {edit_texts}"

    @patch('telegram_bot.Bot')
    @patch('langchain_agent.ModelManager')
    @pytest.mark.asyncio
    async def test_debug_mode_disabled_hides_tool_output(self, mock_model_manager, mock_bot):
        """Test that tool output is hidden when debug mode is disabled."""
        # Mock the model manager
        mock_model_instance = Mock()
        mock_model_manager.return_value.get_default_model.return_value = mock_model_instance
        
        # Create telegram bot (agent is created per-message now)
        telegram_bot = TelegramBot("fake_token", "softcatala_english", max_user_messages=10)
        
        # Ensure debug mode is disabled for test chat (default state)
        chat_id = "12345"
        # debug_mode should be False by default, but let's be explicit
        telegram_bot.debug_mode[chat_id] = False
        
        # Mock the agent's chat_stream method to return tool events
        async def mock_chat_stream(*args, **kwargs):
            yield {"type": "tool_call", "tool": "test_tool", "input": {"param": "value"}, "timestamp": "2023-01-01 12:00:00"}
            yield {"type": "tool_result", "tool": "test_tool", "result": {"status": "success"}, "input": {"param": "value"}, "timestamp": "2023-01-01 12:00:01"}
            yield {"type": "tool_error", "tool": "test_tool", "error": "Test error", "timestamp": "2023-01-01 12:00:02"}
            yield {"type": "content", "content": "Final response"}
        
        # Mock the _create_agent_for_user method to return an agent with our mock chat_stream
        def mock_create_agent_for_user(chat_id):
            mock_agent = Mock()
            mock_agent.chat_stream = mock_chat_stream
            return mock_agent
        telegram_bot._create_agent_for_user = mock_create_agent_for_user
        
        # Mock Telegram update and context
        mock_update = Mock()
        mock_update.effective_chat.id = int(chat_id)
        mock_update.message.text = "Hello bot"
        mock_reply_msg = Mock()
        mock_reply_msg.chat_id = int(chat_id)
        mock_reply_msg.message_id = 123
        mock_reply_msg.edit_text = AsyncMock()
        mock_update.message.reply_text = AsyncMock(return_value=mock_reply_msg)
        
        mock_context = Mock()
        mock_context.bot.send_chat_action = AsyncMock()
        
        # Track all edit calls
        edit_calls = []
        async def track_edit_calls(text, **kwargs):
            edit_calls.append(text)
        mock_reply_msg.edit_text.side_effect = track_edit_calls
        
        # Process the message
        await telegram_bot.handle_message(mock_update, mock_context)
        
        # Verify that tool output was NOT shown (debug mode disabled)
        edit_texts = [call for call in edit_calls]
        
        # Should NOT have detailed tool call message
        tool_call_found = any("🔧 **Eina seleccionada:**" in text for text in edit_texts)
        assert not tool_call_found, f"Tool call message found when debug mode disabled. Edit calls: {edit_texts}"
        
        # Should NOT have detailed tool result message  
        tool_result_found = any("✅ **Eina completada:**" in text for text in edit_texts)
        assert not tool_result_found, f"Tool result message found when debug mode disabled. Edit calls: {edit_texts}"
        
        # Should NOT have detailed tool error message
        tool_error_found = any("❌ **Error d'eina:**" in text for text in edit_texts)
        assert not tool_error_found, f"Tool error message found when debug mode disabled. Edit calls: {edit_texts}"
        
        # Should still have final response
        final_response_found = any("🤖 Final response" in text for text in edit_texts)
        assert final_response_found, f"Final response not found. Edit calls: {edit_texts}"
        
        # Should only have initial thinking message and final response
        # Filter out empty strings and thinking message
        meaningful_edits = [text for text in edit_texts if text and not text.startswith("🤔")]
        assert len(meaningful_edits) == 1, f"Expected only 1 meaningful edit (final response), got {len(meaningful_edits)}: {meaningful_edits}"

    @patch('telegram_bot.Bot')
    @patch('langchain_agent.ModelManager')
    @pytest.mark.asyncio
    async def test_debug_command_toggles_mode(self, mock_model_manager, mock_bot):
        """Test that the /debug command properly toggles debug mode."""
        # Mock the model manager
        mock_model_instance = Mock()
        mock_model_manager.return_value.get_default_model.return_value = mock_model_instance
        
        # Create telegram bot (agent is created per-message now)
        telegram_bot = TelegramBot("fake_token", "softcatala_english", max_user_messages=10)
        
        chat_id = "12345"
        
        # Mock Telegram update and context for debug command
        mock_update = Mock()
        mock_update.effective_chat.id = int(chat_id)
        mock_update.message.reply_text = AsyncMock()
        
        mock_context = Mock()
        
        # Initially debug mode should be False
        assert telegram_bot.debug_mode.get(chat_id, False) == False
        
        # First /debug command should enable debug mode
        await telegram_bot.debug_command(mock_update, mock_context)
        assert telegram_bot.debug_mode.get(chat_id, False) == True
        
        # Verify the message sent
        args, kwargs = mock_update.message.reply_text.call_args
        assert "Mode Debug Activat" in args[0]
        
        # Reset mock
        mock_update.message.reply_text.reset_mock()
        
        # Second /debug command should disable debug mode
        await telegram_bot.debug_command(mock_update, mock_context)
        assert telegram_bot.debug_mode.get(chat_id, False) == False
        
        # Verify the message sent
        args, kwargs = mock_update.message.reply_text.call_args
        assert "Mode Debug Desactivat" in args[0]

    @patch('telegram_bot.Bot')
    @patch('langchain_agent.ModelManager')
    @pytest.mark.asyncio
    async def test_debug_mode_per_chat_isolation(self, mock_model_manager, mock_bot):
        """Test that debug mode is isolated per chat."""
        # Mock the model manager
        mock_model_instance = Mock()
        mock_model_manager.return_value.get_default_model.return_value = mock_model_instance
        
        # Create telegram bot (agent is created per-message now)
        telegram_bot = TelegramBot("fake_token", "softcatala_english", max_user_messages=10)
        
        chat_id_1 = "12345"
        chat_id_2 = "67890"
        
        # Enable debug mode for chat 1 only
        telegram_bot.debug_mode[chat_id_1] = True
        telegram_bot.debug_mode[chat_id_2] = False
        
        # Verify isolation
        assert telegram_bot.debug_mode.get(chat_id_1, False) == True
        assert telegram_bot.debug_mode.get(chat_id_2, False) == False
        
        # Verify a new chat defaults to False
        chat_id_3 = "11111"
        assert telegram_bot.debug_mode.get(chat_id_3, False) == False