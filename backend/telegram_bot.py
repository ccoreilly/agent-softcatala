import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction, ParseMode

from langchain_agent import LangChainAgent
from message_history import MessageHistory

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramBot:
    """
    Telegram bot that integrates with LangChain agent and manages message history.
    """
    
    def __init__(self, token: str, agent: LangChainAgent, max_user_messages: int = 20):
        """
        Initialize the Telegram bot.
        
        Args:
            token: Telegram bot token
            agent: LangChain agent instance
            max_user_messages: Maximum number of user messages to keep in history
        """
        self.token = token
        self.agent = agent
        self.message_history = MessageHistory(max_user_messages)
        self.application = None
        self.bot = Bot(token=token)
        
        # Track ongoing conversations to prevent spam
        self.active_chats: Dict[str, bool] = {}
        # Track last message content to prevent duplicate edits
        self.last_message_content: Dict[str, str] = {}
        # Track debug mode for each chat
        self.debug_mode: Dict[str, bool] = {}
    
    def setup_handlers(self) -> None:
        """Set up command and message handlers."""
        if not self.application:
            return
            
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("clear", self.clear_command))
        self.application.add_handler(CommandHandler("info", self.info_command))
        self.application.add_handler(CommandHandler("debug", self.debug_command))
        self.application.add_handler(CommandHandler("models", self.models_command))
        self.application.add_handler(CommandHandler("model", self.model_command))
        
        # Message handler for regular text messages
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        chat_id = str(update.effective_chat.id)
        user_name = update.effective_user.first_name or "amic"
        
        welcome_message = (
            f"🤖 Hola {user_name}! Benvingut a l'Agent de Softcatalà.\n\n"
            "Puc ajudar-te amb diverses tasques utilitzant capacitats d'IA avançades incloent:\n"
            "• Cerca web i navegació\n"
            "• Consultes a Wikipedia\n"
            "• Respostes a preguntes generals\n"
            "• Assistència amb codi\n"
            "• I molt més!\n\n"
            "Ordres:\n"
            "/help - Mostra aquest missatge d'ajuda\n"
            "/clear - Esborra l'historial de conversa\n"
            "/info - Mostra estadístiques de conversa\n"
            "/debug - Activa/desactiva el mode debug\n"
            "/models - Mostra models disponibles\n"
            "/model [proveïdor] [model] - Canvia el model d'IA\n\n"
            "Simplement envia'm un missatge i l'Agent de Softcatalà farà el seu millor per ajudar-te! 🚀"
        )
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Started conversation with user {chat_id}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_message = (
            "🤖 *Ajuda de l'Agent de Softcatalà*\n\n"
            "*Ordres Disponibles:*\n"
            "/start - Inicia el bot i mostra el missatge de benvinguda\n"
            "/help - Mostra aquest missatge d'ajuda\n"
            "/clear - Esborra el teu historial de conversa\n"
            "/history - Mostra estadístiques de conversa\n"
            "/status - Comprova l'estat del bot i el model d'IA\n"
            "/debug - Activa/desactiva el mode debug detallat\n"
            "/models - Llista tots els models d'IA disponibles\n"
            "/model [proveïdor] [model] - Canvia el model d'IA actual\n\n"
            "*Com utilitzar-lo:*\n"
            "Simplement envia qualsevol missatge i l'Agent de Softcatalà respondrà utilitzant capacitats d'IA avançades.\n"
            "L'Agent pot navegar per la web, cercar a Wikipedia, respondre preguntes, ajudar amb codi, i més!\n\n"
            "*Funcionalitats:*\n"
            "• Manté el context de conversa (fins a 20 dels teus missatges)\n"
            "• Capacitats de navegació web i cerca\n"
            "• Suport per múltiples models d'IA\n"
            "• Integració d'eines per respostes millorades\n\n"
            "No dubtis a preguntar-me qualsevol cosa! 💬"
        )
        
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /clear command to clear conversation history."""
        chat_id = str(update.effective_chat.id)
        
        self.message_history.clear_history(chat_id)
        
        await update.message.reply_text(
            "🗑️ Historial de conversa esborrat! Començant de nou.",
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(f"Cleared history for chat {chat_id}")
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /info command to show conversation statistics."""
        chat_id = str(update.effective_chat.id)
        
        user_messages = self.message_history.get_user_message_count(chat_id)
        total_messages = self.message_history.get_total_message_count(chat_id)

        current_model = self.agent.get_current_model()
        
        history_message = (
            f"📊 *Estadístiques de Conversa*\n\n"
            f"👤 Els teus missatges: {user_messages}\n"
            f"🤖 Missatges totals: {total_messages}\n"
            f"📝 Màxim de missatges d'usuari emmagatzemats: {self.message_history.max_user_messages}\n\n"
            f"🤖 Model actual: {current_model}\n\n"
            f"Utilitza /clear per restablir l'historial de conversa."
        )
        
        await update.message.reply_text(history_message, parse_mode=ParseMode.MARKDOWN)

    async def debug_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /debug command to toggle debug mode."""
        chat_id = str(update.effective_chat.id)
        
        # Toggle debug mode for this chat
        current_debug = self.debug_mode.get(chat_id, False)
        new_debug = not current_debug
        self.debug_mode[chat_id] = new_debug
        
        if new_debug:
            debug_message = (
                "🐛 *Mode Debug Activat*\n\n"
                "Ara mostraré informació detallada sobre:\n"
                "• Crides d'eines i paràmetres\n"
                "• Detalls de peticions HTTP\n"
                "• Estats de resposta i errors\n"
                "• Temps d'execució\n\n"
                "Utilitza `/debug` de nou per desactivar-ho."
            )
        else:
            debug_message = (
                "🐛 *Mode Debug Desactivat*\n\n"
                "Ja no mostraré informació detallada de debug.\n"
                "Utilitza `/debug` per activar-ho de nou."
            )
        
        await update.message.reply_text(debug_message, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Debug mode {'enabled' if new_debug else 'disabled'} for chat {chat_id}")
    
    async def models_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /models command to list available models."""
        try:
            models_info = await self.agent.get_available_models()
            
            models_message = "🧠 *Models d'IA Disponibles*\n\n"
            
            for provider, models in models_info.items():
                if models:  # Only show providers that have models
                    models_message += f"*{provider.upper()}:*\n"
                    for model in models:
                        models_message += f"• `{model}`\n"
                    models_message += "\n"
            
            if not any(models for models in models_info.values()):
                models_message += "❌ No hi ha models disponibles actualment.\n"
            else:
                models_message += "💡 *Ús:* `/model [proveïdor] [model]`\n"
                models_message += "📌 *Exemple:* `/model openrouter openai/gpt-oss-20b:free`"
            
        except Exception as e:
            models_message = f"❌ *Error obtenint la llista de models:*\n{str(e)}"
            logger.error(f"Error in models command: {e}")
        
        await update.message.reply_text(models_message, parse_mode=ParseMode.MARKDOWN)
    
    async def model_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /model command to switch models."""
        try:
            # Parse arguments
            if not context.args or len(context.args) < 2:
                help_message = (
                    "🔧 *Canvi de Model*\n\n"
                    "*Ús:* `/model [proveïdor] [model]`\n\n"
                    "*Exemples:*\n"
                    "• `/model openrouter openai/gpt-oss-20b:free`\n"
                    "• `/model openai gpt-4o-mini`\n"
                    "• `/model ollama llama3.2`\n\n"
                    "📝 *Consell:* Utilitza `/models` per veure tots els models disponibles."
                )
                await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
                return
            
            provider = context.args[0].lower()
            model_name = context.args[1]
            
            # Try to switch the model
            self.agent.switch_model(provider, model_name)
            
            success_message = (
                f"✅ *Model canviat correctament!*\n\n"
                f"🔧 **Proveïdor:** `{provider}`\n"
                f"🧠 **Model:** `{model_name}`\n\n"
                f"Ara pots començar a fer preguntes amb el nou model. 🚀"
            )
            
            await update.message.reply_text(success_message, parse_mode=ParseMode.MARKDOWN)
            logger.info(f"Model switched to {provider}/{model_name} for chat {update.effective_chat.id}")
            
        except ValueError as e:
            error_message = (
                f"❌ *Error de configuració:*\n"
                f"`{str(e)}`\n\n"
                f"💡 Utilitza `/models` per veure els proveïdors i models disponibles."
            )
            await update.message.reply_text(error_message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            error_message = (
                f"❌ *Error canviant el model:*\n"
                f"`{str(e)}`\n\n"
                f"🔄 Si us plau, torna-ho a intentar o utilitza `/models` per veure opcions vàlides."
            )
            logger.error(f"Error in model command: {e}")
            await update.message.reply_text(error_message, parse_mode=ParseMode.MARKDOWN)
    
    def _escape_markdown_v2(self, text: str) -> str:
        """
        Escape special characters for Telegram MarkdownV2.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text safe for MarkdownV2
        """
        # Characters that need escaping in MarkdownV2
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        escaped_text = text
        for char in escape_chars:
            escaped_text = escaped_text.replace(char, f'\\{char}')
        return escaped_text
    
    def _truncate_message(self, content: str, max_length: int = 4000) -> tuple[str, bool]:
        """
        Truncate message content to fit within Telegram's limits.
        
        Args:
            content: Original message content
            max_length: Maximum allowed length (default 4000 to leave room for formatting)
            
        Returns:
            Tuple of (truncated_content, was_truncated)
        """
        if len(content) <= max_length:
            return content, False
        
        # Try to truncate at a word boundary
        truncated = content[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # Only use word boundary if it's not too far back
            truncated = truncated[:last_space]
        
        truncated += "...\n\n⚠️ *Missatge truncat - massa llarg per mostrar completament*"
        return truncated, True
    
    async def _send_split_message(self, chat_id: int, content: str, parse_mode=None) -> list:
        """
        Send a long message by splitting it into multiple parts.
        
        Args:
            chat_id: Chat ID to send messages to
            content: Content to send
            parse_mode: Telegram parse mode
            
        Returns:
            List of sent message objects
        """
        max_length = 4000  # Leave room for formatting
        messages = []
        
        if len(content) <= max_length:
            # Single message
            try:
                msg = await self.bot.send_message(
                    chat_id=chat_id,
                    text=content,
                    parse_mode=parse_mode
                )
                messages.append(msg)
            except Exception as e:
                # Fallback without parse_mode
                msg = await self.bot.send_message(
                    chat_id=chat_id,
                    text=content
                )
                messages.append(msg)
        else:
            # Split into multiple messages
            parts = []
            current_part = ""
            lines = content.split('\n')
            
            for line in lines:
                if len(current_part + line + '\n') <= max_length:
                    current_part += line + '\n'
                else:
                    if current_part:
                        parts.append(current_part.rstrip())
                        current_part = line + '\n'
                    else:
                        # Single line is too long, force split
                        while len(line) > max_length:
                            parts.append(line[:max_length])
                            line = line[max_length:]
                        current_part = line + '\n'
            
            if current_part:
                parts.append(current_part.rstrip())
            
            # Send each part
            for i, part in enumerate(parts):
                part_prefix = f"[{i+1}/{len(parts)}] " if len(parts) > 1 else ""
                try:
                    msg = await self.bot.send_message(
                        chat_id=chat_id,
                        text=part_prefix + part,
                        parse_mode=parse_mode
                    )
                    messages.append(msg)
                except Exception as e:
                    # Fallback without parse_mode
                    msg = await self.bot.send_message(
                        chat_id=chat_id,
                        text=part_prefix + part
                    )
                    messages.append(msg)
                    
                # Small delay between messages to avoid rate limiting
                if i < len(parts) - 1:
                    await asyncio.sleep(0.1)
        
        return messages

    async def safe_edit_message(self, message, new_content: str, parse_mode=None, message_key: str = None) -> bool:
        """
        Safely edit a message, handling errors and falling back to new messages when needed.
        
        Args:
            message: The message object to edit
            new_content: The new content for the message
            parse_mode: Telegram parse mode (optional)
            message_key: Unique key to track this message's content
        
        Returns:
            bool: True if message was edited or sent successfully, False if skipped
        """
        if message_key is None:
            message_key = f"{message.chat_id}_{message.message_id}"
        
        # Check if content is the same as last time
        if message_key in self.last_message_content:
            if self.last_message_content[message_key] == new_content:
                return False  # Skip editing, content is the same
        
        # Truncate message if too long
        truncated_content, was_truncated = self._truncate_message(new_content)
        
        try:
            # Try to edit the existing message
            if parse_mode:
                await message.edit_text(truncated_content, parse_mode=parse_mode)
            else:
                await message.edit_text(truncated_content)
            
            # Track the new content
            self.last_message_content[message_key] = new_content
            return True
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's the "not modified" error specifically
            if "message is not modified" in error_str:
                logger.debug(f"Message content unchanged, skipping edit: {message_key}")
                return False
            
            # Handle specific Telegram API errors
            elif "can't parse entities" in error_str or "bad request" in error_str:
                logger.warning(f"Markdown parsing error for message {message_key}, trying without parse_mode: {e}")
                try:
                    # Retry without parse_mode
                    await message.edit_text(truncated_content)
                    self.last_message_content[message_key] = new_content
                    return True
                except Exception as e2:
                    logger.warning(f"Failed to edit message {message_key} even without parse_mode: {e2}")
                    return await self._fallback_to_new_message(message.chat_id, new_content, parse_mode)
            
            elif "message_too_long" in error_str or "message is too long" in error_str:
                logger.warning(f"Message too long for edit {message_key}, sending as new message(s)")
                return await self._fallback_to_new_message(message.chat_id, new_content, parse_mode)
            
            else:
                logger.warning(f"Failed to edit message {message_key}: {e}")
                return await self._fallback_to_new_message(message.chat_id, new_content, parse_mode)
    
    async def _fallback_to_new_message(self, chat_id: int, content: str, parse_mode=None) -> bool:
        """
        Fallback method to send content as new message(s) when editing fails.
        
        Args:
            chat_id: Chat ID to send to
            content: Content to send
            parse_mode: Telegram parse mode
            
        Returns:
            bool: True if messages were sent successfully
        """
        try:
            messages = await self._send_split_message(chat_id, content, parse_mode)
            logger.info(f"Sent {len(messages)} fallback message(s) to chat {chat_id}")
            return len(messages) > 0
        except Exception as e:
            logger.error(f"Failed to send fallback message to chat {chat_id}: {e}")
            try:
                # Last resort: send simple text message
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Ho sento, hi ha hagut un problema mostrant la resposta completa."
                )
                return True
            except Exception as e2:
                logger.error(f"Failed to send error message to chat {chat_id}: {e2}")
                return False
    
    def cleanup_old_message_tracking(self, max_entries: int = 1000) -> None:
        """
        Clean up old message content tracking to prevent memory leaks.
        
        Args:
            max_entries: Maximum number of entries to keep
        """
        if len(self.last_message_content) > max_entries:
            # Remove oldest entries (simple approach - remove first half)
            keys_to_remove = list(self.last_message_content.keys())[:len(self.last_message_content) // 2]
            for key in keys_to_remove:
                self.last_message_content.pop(key, None)
            logger.info(f"Cleaned up {len(keys_to_remove)} old message tracking entries")
    
    def _filter_tool_information(self, content: str, debug_enabled: bool) -> str:
        """
        Filter out tool call and output information from content when debug is disabled.
        
        Args:
            content: The content to filter
            debug_enabled: Whether debug mode is enabled
            
        Returns:
            Filtered content with tool information removed if debug is disabled
        """
        if debug_enabled:
            return content
        
        import re
        
        # Remove tool_code blocks
        content = re.sub(r'tool_code\s*\n.*?\n\n', '', content, flags=re.DOTALL)
        
        # Remove tool_output blocks
        content = re.sub(r'tool_output\s*\n.*?\n\n', '', content, flags=re.DOTALL)
        
        # Remove standalone "tool_code" and "tool_output" lines
        content = re.sub(r'\n\s*tool_code\s*\n', '\n', content)
        content = re.sub(r'\n\s*tool_output\s*\n', '\n', content)
        
        # Clean up extra newlines that might be left
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content.strip()
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle regular text messages."""
        chat_id = str(update.effective_chat.id)
        user_message = update.message.text
        
        # Check if we're already processing a message for this chat
        if self.active_chats.get(chat_id, False):
            await update.message.reply_text(
                "⏳ Si us plau espera, encara estic processant el teu missatge anterior..."
            )
            return
        
        try:
            # Mark chat as active
            self.active_chats[chat_id] = True
            
            # Periodic cleanup of message tracking (every 100 messages)
            if len(self.last_message_content) > 100 and len(self.last_message_content) % 100 == 0:
                self.cleanup_old_message_tracking()
            
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            
            # Add user message to history
            self.message_history.add_message(chat_id, "user", user_message)
            
            # Get conversation history for context
            history = self.message_history.get_history(chat_id)
            
            # Send message to agent with streaming
            response_parts = []
            full_response = ""
            
            # Send initial "thinking" message
            thinking_msg = await update.message.reply_text("🤔 Pensant...")
            
            try:
                async for chunk in self.agent.chat_stream(history, chat_id):
                    chunk_type = chunk.get("type")
                    
                    if chunk_type == "content":
                        content = chunk.get("content", "")
                        if content:
                            full_response += content
                            response_parts.append(content)
                    
                    elif chunk_type == "tool_call":
                        # Check if debug mode is enabled for this chat
                        debug_enabled = self.debug_mode.get(chat_id, False)
                        
                        # Only show tool call messages when debug mode is enabled
                        if debug_enabled:
                            tool_name = chunk.get("tool", "unknown")
                            tool_input = chunk.get("input", {})
                            timestamp = chunk.get("timestamp", "")
                            
                            # Create detailed tool call message
                            tool_msg = f"🔧 **Eina seleccionada:** `{tool_name}`\n"
                            tool_msg += f"⏰ **Hora:** {timestamp}\n"
                            
                            # Format tool parameters in a readable way
                            if tool_input:
                                tool_msg += f"📋 **Paràmetres:**\n"
                                for key, value in tool_input.items():
                                    # Truncate long values
                                    value_str = str(value)
                                    if len(value_str) > 50:
                                        value_str = value_str[:47] + "..."
                                    tool_msg += f"   • `{key}`: `{value_str}`\n"
                            else:
                                tool_msg += f"📋 **Paràmetres:** Cap\n"
                            
                            tool_msg += "⏳ **Estat:** Executant eina..."
                            
                            # Send as new message instead of editing
                            await self._send_split_message(
                                chat_id=int(chat_id),
                                content=tool_msg,
                                parse_mode=ParseMode.MARKDOWN
                            )
                    
                    elif chunk_type == "tool_result":
                        # Check if debug mode is enabled for this chat
                        debug_enabled = self.debug_mode.get(chat_id, False)
                        
                        # Only show tool result messages when debug mode is enabled
                        if debug_enabled:
                            tool_name = chunk.get("tool", "unknown")
                            result = chunk.get("result", {})
                            tool_input = chunk.get("input", {})
                            timestamp = chunk.get("timestamp", "")
                            
                            # Create detailed tool result message
                            result_msg = f"✅ **Eina completada:** `{tool_name}`\n"
                            result_msg += f"⏰ **Hora:** {timestamp}\n"
                            
                            # Show input parameters that were used
                            if tool_input:
                                result_msg += f"📥 **Paràmetres utilitzats:**\n"
                                for key, value in tool_input.items():
                                    value_str = str(value)
                                    if len(value_str) > 30:
                                        value_str = value_str[:27] + "..."
                                    result_msg += f"   • `{key}`: `{value_str}`\n"
                            
                            # Show result status and content
                            if isinstance(result, dict):
                                status = result.get("status", "unknown")
                                if status == "success":
                                    result_msg += "✅ **Estat:** Èxit\n"
                                    
                                    # Show specific result details based on tool
                                    if tool_name == "catalan_synonyms":
                                        results_data = result.get("results", [])
                                        if results_data:
                                            synonym_count = sum(len(r.get("synonyms", [])) for r in results_data)
                                            result_msg += f"📊 **Resultats:** {len(results_data)} entrades, {synonym_count} grups de sinònims\n"
                                        word = result.get("word", "")
                                        if word:
                                            result_msg += f"🔍 **Paraula cercada:** `{word}`\n"
                                    elif tool_name == "catalan_spell_checker":
                                        corrections = result.get("corrections", [])
                                        if corrections:
                                            result_msg += f"📝 **Correccions:** {len(corrections)} suggeriments\n"
                                    else:
                                        # Generic result info
                                        result_keys = [k for k in result.keys() if k not in ["status", "timestamp"]]
                                        if result_keys:
                                            result_msg += f"📤 **Claus de resposta:** {', '.join(result_keys[:3])}\n"
                                        
                                elif status == "error":
                                    result_msg += "❌ **Estat:** Error\n"
                                    if "error" in result:
                                        error_text = result["error"]
                                        if len(error_text) > 100:
                                            error_text = error_text[:97] + "..."
                                        result_msg += f"⚠️ **Error:** `{error_text}`\n"
                                elif status == "not_found":
                                    result_msg += "🔍 **Estat:** No trobat\n"
                                    if "message" in result:
                                        result_msg += f"💬 **Missatge:** {result['message']}\n"
                                else:
                                    result_msg += f"📊 **Estat:** `{status}`\n"
                            else:
                                # Non-dict result
                                result_str = str(result)
                                if len(result_str) > 150:
                                    result_str = result_str[:147] + "..."
                                result_msg += f"📤 **Resposta:** `{result_str}`\n"
                            
                            result_msg += "🤔 **Estat:** Processant resultats..."
                            
                            # Send as new message instead of editing
                            await self._send_split_message(
                                chat_id=int(chat_id),
                                content=result_msg,
                                parse_mode=ParseMode.MARKDOWN
                            )
                    
                    elif chunk_type == "tool_error":
                        # Check if debug mode is enabled for this chat
                        debug_enabled = self.debug_mode.get(chat_id, False)
                        
                        # Only show tool error messages when debug mode is enabled
                        if debug_enabled:
                            tool_name = chunk.get("tool", "unknown")
                            error_msg = chunk.get("error", "Error desconegut")
                            timestamp = chunk.get("timestamp", "")
                            
                            # Create detailed tool error message
                            tool_error_msg = f"❌ **Error d'eina:** `{tool_name}`\n"
                            tool_error_msg += f"⏰ **Hora:** {timestamp}\n"
                            tool_error_msg += f"⚠️ **Error:** `{error_msg[:200]}{'...' if len(error_msg) > 200 else ''}`\n"
                            tool_error_msg += "🔄 Continuant sense aquesta eina..."
                            
                            # Send as new message instead of editing
                            await self._send_split_message(
                                chat_id=int(chat_id),
                                content=tool_error_msg,
                                parse_mode=ParseMode.MARKDOWN
                            )
                    
                    elif chunk_type == "error":
                        error_msg = chunk.get("error", "Error desconegut")
                        timestamp = chunk.get("timestamp", "")
                        message_key = f"{thinking_msg.chat_id}_{thinking_msg.message_id}"
                        
                        # Create detailed general error message
                        general_error_msg = f"❌ **Error general:**\n"
                        general_error_msg += f"⏰ **Hora:** {timestamp}\n"
                        general_error_msg += f"⚠️ **Detalls:** `{error_msg[:200]}{'...' if len(error_msg) > 200 else ''}`"
                        
                        await self.safe_edit_message(
                            thinking_msg,
                            general_error_msg,
                            parse_mode=ParseMode.MARKDOWN,
                            message_key=message_key
                        )
                        return
                
                # Final response - send as new message instead of editing
                if full_response:
                    # Filter tool information if debug is disabled
                    debug_enabled = self.debug_mode.get(chat_id, False)
                    filtered_response = self._filter_tool_information(full_response, debug_enabled)
                    
                    # Send the response as a new message
                    await self._send_split_message(
                        chat_id=int(chat_id),
                        content=f"🤖 {filtered_response}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                    # Delete or update the thinking message to show completion
                    message_key = f"{thinking_msg.chat_id}_{thinking_msg.message_id}"
                    await self.safe_edit_message(
                        thinking_msg,
                        "✅ Resposta completada",
                        message_key=message_key
                    )
                    
                    # Add assistant response to history (use filtered response)
                    self.message_history.add_message(chat_id, "assistant", filtered_response)
                else:
                    # Send error as new message
                    await self._send_split_message(
                        chat_id=int(chat_id),
                        content="🤖 Ho sento, no he pogut generar una resposta."
                    )
                    
                    # Update thinking message to show error
                    message_key = f"{thinking_msg.chat_id}_{thinking_msg.message_id}"
                    await self.safe_edit_message(
                        thinking_msg,
                        "❌ Error en la generació de resposta",
                        message_key=message_key
                    )
                
            except Exception as e:
                logger.error(f"Error during agent streaming: {e}")
                message_key = f"{thinking_msg.chat_id}_{thinking_msg.message_id}"
                await self.safe_edit_message(
                    thinking_msg,
                    f"❌ Ho sento, he trobat un error: {str(e)}",
                    message_key=message_key
                )
        
        except Exception as e:
            logger.error(f"Error handling message from {chat_id}: {e}")
            await update.message.reply_text(
                "❌ Ho sento, he trobat un error processant el teu missatge. Si us plau, torna-ho a intentar."
            )
        
        finally:
            # Mark chat as no longer active
            self.active_chats[chat_id] = False
            
            # Clean up message content tracking for this conversation
            # Remove entries that match the current thinking message
            if 'thinking_msg' in locals():
                message_key = f"{thinking_msg.chat_id}_{thinking_msg.message_id}"
                self.last_message_content.pop(message_key, None)
    
    async def start_bot(self) -> None:
        """Start the Telegram bot."""
        try:
            # Create application
            self.application = Application.builder().token(self.token).build()
            
            # Set up handlers
            self.setup_handlers()
            
            # Start the bot
            logger.info("Starting Telegram bot...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Telegram bot is running!")
            
            # Keep the bot running until cancelled
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("Telegram bot cancelled, shutting down...")
                raise
                
        except asyncio.CancelledError:
            logger.info("Telegram bot task was cancelled")
            raise
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}")
            raise
        finally:
            if self.application:
                try:
                    logger.info("Stopping Telegram bot application...")
                    
                    # Stop polling first to prevent network errors
                    if self.application.updater and self.application.updater.running:
                        logger.info("Stopping updater...")
                        await self.application.updater.stop()
                    
                    # Then stop the application
                    if self.application.running:
                        await self.application.stop()
                    
                    # Finally shutdown
                    await self.application.shutdown()
                    logger.info("Telegram bot stopped successfully")
                except Exception as e:
                    logger.error(f"Error stopping Telegram bot: {e}")
                    # Don't re-raise to avoid masking the original cancellation
    
    async def stop_bot(self) -> None:
        """Stop the Telegram bot."""
        if self.application:
            logger.info("Stopping Telegram bot...")
            await self.application.stop()
            logger.info("Telegram bot stopped.")