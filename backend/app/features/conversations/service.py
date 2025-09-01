"""Conversations service - conversation management business logic"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from app.shared.models import Message
from .models import Conversation, ConversationSummary, ConversationListRequest
from .repository import ConversationRepository

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self):
        self.repository = ConversationRepository()

    async def create_conversation(self, title: Optional[str] = None) -> Conversation:
        try:
            logger.info(f"Creating new conversation with title: {title}")

            conversation = Conversation(
                title=title,
                messages=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            created_conversation = await self.repository.create(conversation)
            logger.info(f"Created conversation: {created_conversation.id}")
            return created_conversation

        except Exception as e:
            logger.error(f"Failed to create conversation: {str(e)}")
            raise Exception(f"Failed to create conversation: {str(e)}")

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        try:
            logger.info(f"Retrieving conversation: {conversation_id}")
            conversation = await self.repository.get_by_id(conversation_id)

            if conversation:
                logger.info(
                    f"Found conversation with {len(conversation.messages)} messages"
                )
            else:
                logger.warning(f"Conversation not found: {conversation_id}")

            return conversation

        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {str(e)}")
            return None

    async def get_conversations(
        self, request: ConversationListRequest
    ) -> List[ConversationSummary]:
        try:
            logger.info(
                f"Getting conversations: skip={request.skip}, limit={request.limit}"
            )

            if request.include_messages:
                # Get full conversations
                full_conversations = await self.repository.find_all(
                    skip=request.skip, limit=request.limit
                )

                # Convert to summaries
                summaries = []
                for conv in full_conversations:
                    summary = ConversationSummary(
                        id=conv.id,
                        title=conv.title,
                        message_count=conv.get_message_count(),
                        last_message_preview=conv.get_latest_message().content[:100]
                        if conv.get_latest_message()
                        else None,
                        created_at=conv.created_at,
                        updated_at=conv.updated_at,
                    )
                    summaries.append(summary)

                return summaries
            else:
                # Get lightweight summaries (more efficient)
                return await self.repository.get_conversation_summaries(
                    skip=request.skip, limit=request.limit
                )

        except Exception as e:
            logger.error(f"Failed to get conversations: {str(e)}")
            return []

    async def update_conversation_title(
        self, conversation_id: str, title: str
    ) -> Optional[Conversation]:
        try:
            logger.info(f"Updating title for conversation {conversation_id}: {title}")

            updated_conversation = await self.repository.update_title(
                conversation_id, title
            )

            if updated_conversation:
                logger.info("Successfully updated conversation title")
            else:
                logger.warning("Failed to update title - conversation not found")

            return updated_conversation

        except Exception as e:
            logger.error(f"Failed to update conversation title: {str(e)}")
            return None

    async def delete_conversation(self, conversation_id: str) -> bool:
        try:
            logger.info(f"Deleting conversation: {conversation_id}")

            success = await self.repository.delete(conversation_id)

            if success:
                logger.info(f"Successfully deleted conversation: {conversation_id}")
            else:
                logger.warning(
                    f"Failed to delete conversation - not found: {conversation_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {str(e)}")
            return False

    async def add_message(
        self, conversation_id: str, message: Message
    ) -> Optional[Conversation]:
        try:
            logger.info(
                f"Adding {message.role.value} message to conversation {conversation_id}"
            )

            updated_conversation = await self.repository.add_message_to_conversation(
                conversation_id, message
            )

            if updated_conversation:
                logger.info(
                    f"Message added successfully. Total messages: {len(updated_conversation.messages)}"
                )
            else:
                logger.warning(
                    f"Failed to add message - conversation not found: {conversation_id}"
                )

            return updated_conversation

        except Exception as e:
            logger.error(f"Failed to add message to conversation: {str(e)}")
            return None
