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
logging.basicConfig(
    level=logging.INFO,
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
    
    def setup_handlers(self) -> None:
        """Set up command and message handlers."""
        if not self.application:
            return
            
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("clear", self.clear_command))
        self.application.add_handler(CommandHandler("history", self.history_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
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
            "/history - Mostra estadístiques de conversa\n"
            "/status - Comprova l'estat del bot i l'IA\n\n"
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
            "/status - Comprova l'estat del bot i el model d'IA\n\n"
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
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /history command to show conversation statistics."""
        chat_id = str(update.effective_chat.id)
        
        user_messages = self.message_history.get_user_message_count(chat_id)
        total_messages = self.message_history.get_total_message_count(chat_id)
        
        history_message = (
            f"📊 *Estadístiques de Conversa*\n\n"
            f"👤 Els teus missatges: {user_messages}\n"
            f"🤖 Missatges totals: {total_messages}\n"
            f"📝 Màxim de missatges d'usuari emmagatzemats: {self.message_history.max_user_messages}\n\n"
            f"Utilitza /clear per restablir l'historial de conversa."
        )
        
        await update.message.reply_text(history_message, parse_mode=ParseMode.MARKDOWN)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command to show bot and AI status."""
        try:
            # Check agent health
            health_status = await self.agent.check_health()
            
            models_info = health_status.get("models", {})
            tools_info = health_status.get("tools", {})
            
            status_message = "🔍 *Estat del Bot*\n\n"
            
            # Model status
            status_message += "🧠 *Models d'IA:*\n"
            for provider, info in models_info.items():
                if isinstance(info, dict):
                    status = info.get("status", "unknown")
                    if status == "available":
                        status_ca = "disponible"
                    elif status == "unavailable":
                        status_ca = "no disponible"
                    else:
                        status_ca = "desconegut"
                    emoji = "✅" if status == "available" else "❌"
                    status_message += f"{emoji} {provider}: {status_ca}\n"
            
            # Tools status
            status_message += f"\n🛠️ *Eines Disponibles:* {tools_info.get('count', 0)}\n"
            for tool_name in tools_info.get('names', []):
                status_message += f"• {tool_name}\n"
            
            # Bot info
            status_message += f"\n🤖 *Informació del Bot:*\n"
            status_message += f"• Xats actius: {len(self.message_history.get_chat_ids())}\n"
            status_message += f"• Bot funcionant: ✅\n"
            
        except Exception as e:
            status_message = f"❌ *Error comprovant l'estat:*\n{str(e)}"
            logger.error(f"Error in status command: {e}")
        
        await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)
    
    async def safe_edit_message(self, message, new_content: str, parse_mode=None, message_key: str = None) -> bool:
        """
        Safely edit a message, avoiding duplicate content errors.
        
        Args:
            message: The message object to edit
            new_content: The new content for the message
            parse_mode: Telegram parse mode (optional)
            message_key: Unique key to track this message's content
        
        Returns:
            bool: True if message was edited successfully, False if skipped or failed
        """
        if message_key is None:
            message_key = f"{message.chat_id}_{message.message_id}"
        
        # Check if content is the same as last time
        if message_key in self.last_message_content:
            if self.last_message_content[message_key] == new_content:
                return False  # Skip editing, content is the same
        
        try:
            if parse_mode:
                await message.edit_text(new_content, parse_mode=parse_mode)
            else:
                await message.edit_text(new_content)
            
            # Track the new content
            self.last_message_content[message_key] = new_content
            return True
            
        except Exception as e:
            # Check if it's the "not modified" error specifically
            if "Message is not modified" in str(e):
                logger.debug(f"Message content unchanged, skipping edit: {message_key}")
                return False
            else:
                logger.warning(f"Failed to edit message {message_key}: {e}")
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
                            
                            # Update message every few chunks or when we have substantial content
                            if len(response_parts) % 3 == 0 or len(full_response) > 100:
                                message_key = f"{thinking_msg.chat_id}_{thinking_msg.message_id}"
                                # Try with markdown first
                                success = await self.safe_edit_message(
                                    thinking_msg,
                                    f"🤖 {full_response}",
                                    parse_mode=ParseMode.MARKDOWN,
                                    message_key=message_key
                                )
                                # If markdown fails, try without it
                                if not success:
                                    await self.safe_edit_message(
                                        thinking_msg,
                                        f"🤖 {full_response}",
                                        message_key=message_key
                                    )
                    
                    elif chunk_type == "tool_call":
                        tool_name = chunk.get("tool", "unknown")
                        message_key = f"{thinking_msg.chat_id}_{thinking_msg.message_id}"
                        await self.safe_edit_message(
                            thinking_msg,
                            f"🔧 Utilitzant eina: {tool_name}...",
                            message_key=message_key
                        )
                    
                    elif chunk_type == "tool_result":
                        message_key = f"{thinking_msg.chat_id}_{thinking_msg.message_id}"
                        await self.safe_edit_message(
                            thinking_msg,
                            "🤔 Processant resultats d'eines...",
                            message_key=message_key
                        )
                    
                    elif chunk_type == "error":
                        error_msg = chunk.get("error", "Error desconegut")
                        message_key = f"{thinking_msg.chat_id}_{thinking_msg.message_id}"
                        await self.safe_edit_message(
                            thinking_msg,
                            f"❌ Error: {error_msg}",
                            message_key=message_key
                        )
                        return
                
                # Final response
                if full_response:
                    message_key = f"{thinking_msg.chat_id}_{thinking_msg.message_id}"
                    # Try with markdown first
                    success = await self.safe_edit_message(
                        thinking_msg,
                        f"🤖 {full_response}",
                        parse_mode=ParseMode.MARKDOWN,
                        message_key=message_key
                    )
                    # If markdown fails, try without it
                    if not success:
                        await self.safe_edit_message(
                            thinking_msg,
                            f"🤖 {full_response}",
                            message_key=message_key
                        )
                    
                    # Add assistant response to history
                    self.message_history.add_message(chat_id, "assistant", full_response)
                else:
                    message_key = f"{thinking_msg.chat_id}_{thinking_msg.message_id}"
                    await self.safe_edit_message(
                        thinking_msg,
                        "🤖 Ho sento, no he pogut generar una resposta.",
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
            
            # Keep the bot running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}")
            raise
        finally:
            if self.application:
                await self.application.stop()
    
    async def stop_bot(self) -> None:
        """Stop the Telegram bot."""
        if self.application:
            logger.info("Stopping Telegram bot...")
            await self.application.stop()
            logger.info("Telegram bot stopped.")