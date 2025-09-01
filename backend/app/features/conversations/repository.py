from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

from app.shared.database import get_database, BaseRepository
from app.shared.models import Message
from .models import Conversation, ConversationSummary

logger = logging.getLogger(__name__)


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self):
        db = get_database()
        super().__init__(db.conversations)

    def _to_domain(self, doc: Dict[str, Any]) -> Conversation:
        """Convert database document to Conversation model"""
        # Convert message dicts to Message objects
        messages = []
        for msg_dict in doc.get("messages", []):
            message = Message(
                role=msg_dict["role"],
                content=msg_dict["content"],
                timestamp=msg_dict.get("timestamp", datetime.now(timezone.utc)),
                metadata=msg_dict.get("metadata"),
            )
            messages.append(message)

        return Conversation(
            id=doc["_id"],
            title=doc.get("title"),
            messages=messages,
            created_at=doc.get("created_at", datetime.now(timezone.utc)),
            updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
        )

    def _to_document(self, conversation: Conversation) -> Dict[str, Any]:
        """Convert Conversation model to database document"""
        # Convert Message objects to dicts
        message_dicts = []
        for msg in conversation.messages:
            message_dict = {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "metadata": msg.metadata,
            }
            message_dicts.append(message_dict)

        doc = {
            "title": conversation.title,
            "messages": message_dicts,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        }

        if conversation.id:
            doc["_id"] = conversation.id

        return doc

    async def get_conversation_summaries(
        self, skip: int = 0, limit: int = 20
    ) -> List[ConversationSummary]:
        """Get lightweight conversation summaries for listing"""
        try:
            pipeline = [
                # Sort by most recent first
                {"$sort": {"updated_at": -1}},
                # Skip and limit
                {"$skip": skip},
                {"$limit": limit},
                # Project only needed fields
                {
                    "$project": {
                        "_id": 1,
                        "title": 1,
                        "created_at": 1,
                        "updated_at": 1,
                        "message_count": {"$size": "$messages"},
                        "last_message": {"$arrayElemAt": ["$messages.content", -1]},
                    }
                },
            ]

            cursor = self.collection.aggregate(pipeline)
            docs = await cursor.to_list(length=limit)

            summaries = []
            for doc in docs:
                summary = ConversationSummary(
                    id=str(doc["_id"]),
                    title=doc.get("title"),
                    message_count=doc.get("message_count", 0),
                    last_message_preview=doc.get("last_message", "")[:100]
                    if doc.get("last_message")
                    else None,
                    created_at=doc.get("created_at", datetime.now(timezone.utc)),
                    updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
                )
                summaries.append(summary)

            logger.info(f"Retrieved {len(summaries)} conversation summaries")
            return summaries

        except Exception as e:
            logger.error(f"Failed to get conversation summaries: {str(e)}")
            return []

    async def update_title(
        self, conversation_id: str, title: str
    ) -> Optional[Conversation]:
        try:
            from bson import ObjectId

            result = await self.collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": {"title": title, "updated_at": datetime.now(timezone.utc)}},
            )

            if result.modified_count > 0:
                logger.info(f"Updated title for conversation {conversation_id}")
                return await self.get_by_id(conversation_id)

            logger.warning(f"No conversation found to update: {conversation_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to update conversation title: {str(e)}")
            return None

    async def add_message_to_conversation(
        self, conversation_id: str, message: Message
    ) -> Optional[Conversation]:
        """Add a message to existing conversation"""
        try:
            from bson import ObjectId

            message_dict = {
                "role": message.role.value,
                "content": message.content,
                "timestamp": message.timestamp,
                "metadata": message.metadata,
            }

            result = await self.collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$push": {"messages": message_dict},
                    "$set": {"updated_at": message.timestamp},
                },
            )

            if result.modified_count > 0:
                logger.info(f"Added message to conversation {conversation_id}")
                return await self.get_by_id(conversation_id)

            logger.warning(f"No conversation found: {conversation_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to add message: {str(e)}")
            return None
