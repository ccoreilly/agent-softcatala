from collections import deque
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MessageHistory:
    """
    Manages message history for Telegram bot with rolling window functionality.
    Keeps a maximum of 20 user messages with all agent messages in between.
    """
    
    def __init__(self, max_user_messages: int = 20):
        self.max_user_messages = max_user_messages
        # Dict mapping chat_id to message history
        self.histories: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_message(self, chat_id: str, role: str, content: str, timestamp: Optional[str] = None) -> None:
        """
        Add a message to the history for a specific chat.
        
        Args:
            chat_id: Unique identifier for the chat/user
            role: Message role ("user" or "assistant")
            content: Message content
            timestamp: Optional timestamp (defaults to current time)
        """
        if chat_id not in self.histories:
            self.histories[chat_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp or datetime.now().isoformat()
        }
        
        self.histories[chat_id].append(message)
        
        # Apply rolling window for user messages only
        if role == "user":
            self._apply_rolling_window(chat_id)
    
    def _apply_rolling_window(self, chat_id: str) -> None:
        """
        Apply rolling window logic: keep only the last max_user_messages user messages
        along with all agent messages that occur between them.
        """
        history = self.histories[chat_id]
        
        # Find positions of user messages
        user_message_indices = []
        for i, msg in enumerate(history):
            if msg["role"] == "user":
                user_message_indices.append(i)
        
        # If we have more user messages than allowed, trim the history
        if len(user_message_indices) > self.max_user_messages:
            # Keep only the last max_user_messages user messages
            excess_user_messages = len(user_message_indices) - self.max_user_messages
            
            # Find the index from which to start keeping messages
            # This will be the index of the (excess_user_messages + 1)th user message
            start_index = user_message_indices[excess_user_messages]
            
            # Trim the history
            self.histories[chat_id] = history[start_index:]
            
            logger.info(f"Trimmed history for chat {chat_id}: removed {start_index} messages, "
                       f"kept {len(self.histories[chat_id])} messages")
    
    def get_history(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        Get the message history for a specific chat.
        
        Args:
            chat_id: Unique identifier for the chat/user
            
        Returns:
            List of messages in chronological order
        """
        return self.histories.get(chat_id, [])
    
    def clear_history(self, chat_id: str) -> None:
        """
        Clear the message history for a specific chat.
        
        Args:
            chat_id: Unique identifier for the chat/user
        """
        if chat_id in self.histories:
            del self.histories[chat_id]
            logger.info(f"Cleared history for chat {chat_id}")
    
    def get_user_message_count(self, chat_id: str) -> int:
        """
        Get the number of user messages for a specific chat.
        
        Args:
            chat_id: Unique identifier for the chat/user
            
        Returns:
            Number of user messages
        """
        history = self.histories.get(chat_id, [])
        return sum(1 for msg in history if msg["role"] == "user")
    
    def get_total_message_count(self, chat_id: str) -> int:
        """
        Get the total number of messages for a specific chat.
        
        Args:
            chat_id: Unique identifier for the chat/user
            
        Returns:
            Total number of messages
        """
        return len(self.histories.get(chat_id, []))
    
    def get_chat_ids(self) -> List[str]:
        """
        Get all chat IDs that have message history.
        
        Returns:
            List of chat IDs
        """
        return list(self.histories.keys())