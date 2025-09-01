from typing import List, Dict, Any
import logging
from app.shared.database import get_database
from app.shared.models import Message
from bson import ObjectId

logger = logging.getLogger(__name__)


class ChatRepository:
    """Repository for chat-specific database operations"""

    def __init__(self):
        self.db = get_database()
        self.conversations_collection = self.db.conversations

    async def add_message_to_conversation(
        self, conversation_id: str, message: Message
    ) -> bool:
        try:
            message_dict = {
                "role": message.role.value,
                "content": message.content,
                "timestamp": message.timestamp,
                "metadata": message.metadata,
            }

            # Add message to conversation
            result = await self.conversations_collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$push": {"messages": message_dict},
                    "$set": {"updated_at": message.timestamp},
                },
            )

            success = result.modified_count > 0
            if success:
                logger.info(f"Added message to conversation {conversation_id}")
            else:
                logger.warning(f"No conversation found with ID {conversation_id}")

            return success

        except Exception as e:
            logger.error(
                f"Failed to add message to conversation {conversation_id}: {str(e)}"
            )
            return False

    async def get_recent_messages(
        self, conversation_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        try:
            conversation = await self.conversations_collection.find_one(
                {"_id": ObjectId(conversation_id)},
                {"messages": {"$slice": -limit}},  # Get last N messages
            )

            if conversation and "messages" in conversation:
                logger.info(
                    f"Retrieved {len(conversation['messages'])} recent messages"
                )
                return conversation["messages"]

            logger.warning(f"No messages found for conversation {conversation_id}")
            return []

        except Exception as e:
            logger.error(
                f"Failed to get recent messages for {conversation_id}: {str(e)}"
            )
            return []

    async def conversation_exists(self, conversation_id: str) -> bool:
        try:
            count = await self.conversations_collection.count_documents(
                {"_id": ObjectId(conversation_id)}
            )
            return count > 0

        except Exception as e:
            logger.error(
                f"Failed to check if conversation exists {conversation_id}: {str(e)}"
            )
            return False
