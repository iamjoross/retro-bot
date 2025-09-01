import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Query

from .models import (
    Conversation,
    ConversationSummary,
    ConversationListRequest,
    ConversationUpdateRequest,
)
from .service import ConversationService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/conversations",
    response_model=Conversation,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation() -> Conversation:
    """
    Create a new chat session.

    Creates a new conversation with no initial messages.
    Returns the created conversation with its unique ID.
    """
    from datetime import datetime

    try:
        logger.info("POST create new conversation")

        # Generate title with current date and time
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = f"Main Title {current_datetime}"

        service = ConversationService()
        conversation = await service.create_conversation(title=title)

        logger.info(f"Created new conversation: {conversation.id}")
        return conversation

    except Exception as e:
        logger.error(f"Failed to create conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


@router.get(
    "/conversations",
    response_model=List[ConversationSummary],
)
async def get_conversations(
    skip: int = Query(0, ge=0, description="Number of conversations to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max conversations to return"),
    include_messages: bool = Query(False, description="Include full message content"),
) -> List[ConversationSummary]:
    """
    Get list of conversations.

    Returns conversation summaries by default for better performance.
    Use `include_messages=true` to get full conversation data.
    """
    try:
        logger.info(
            f"GET conversations: skip={skip}, limit={limit}, include_messages={include_messages}"
        )

        request = ConversationListRequest(
            skip=skip, limit=limit, include_messages=include_messages
        )

        service = ConversationService()
        conversations = await service.get_conversations(request)

        logger.info(f"Retrieved {len(conversations)} conversations")
        return conversations

    except Exception as e:
        logger.error(f"Failed to get conversations: {str(e)}")
        return []


@router.get(
    "/conversations/{conversation_id}",
    response_model=Conversation,
)
async def get_conversation(conversation_id: str) -> Conversation:
    """
    Get a specific conversation by ID with all messages.
    """
    try:
        logger.info(f"GET conversation: {conversation_id}")

        service = ConversationService()
        conversation = await service.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        logger.info(
            f"Retrieved conversation with {len(conversation.messages)} messages"
        )
        return conversation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation",
        )


@router.patch("/conversations/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: str,
    update_request: ConversationUpdateRequest,
) -> Conversation:
    """
    Update conversation properties (currently only title).
    """
    try:
        logger.info(f"PATCH conversation {conversation_id}: {update_request.dict()}")

        service = ConversationService()

        # Currently only title updates are supported
        if update_request.title is not None:
            conversation = await service.update_conversation_title(
                conversation_id, update_request.title
            )

            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found",
                )

            logger.info(f"Updated conversation title: {update_request.title}")
            return conversation

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid update fields provided",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation",
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str) -> dict:
    """
    Delete a conversation and all its messages.
    """
    try:
        logger.info(f"DELETE conversation: {conversation_id}")

        service = ConversationService()
        success = await service.delete_conversation(conversation_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        logger.info(f"Successfully deleted conversation: {conversation_id}")
        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation",
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the conversations service.
    """
    return {
        "service": "conversations",
        "status": "operational",
        "description": "Conversation management service is running",
    }
