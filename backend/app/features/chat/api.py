import logging
from fastapi import APIRouter, HTTPException, status
from .models import ChatRequest, ChatResponse
from .service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse, summary="Chat with DATACOM-7")
async def chat_with_datacom7(request: ChatRequest) -> ChatResponse:
    """
    Send a message to DATACOM-7 and get a response.

    - **message**: The message to send to DATACOM-7 (1-2000 characters)
    - **conversation_id**: Optional ID of existing conversation, or None for new conversation

    Returns DATACOM-7's response with conversation ID and timestamp.
    """
    logger.info(f"🤖 DATACOM-7 Chat API: {request.message[:50]}...")

    try:
        chat_service = ChatService()
        response = await chat_service.process_chat(request)

        logger.info(f"✅ Chat response generated: {len(response.message)} chars")
        return response

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Internal chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DATACOM-7 system malfunction. Please retry.",
        )


@router.get("/health", summary="Chat service health check")
async def health_check():
    """
    Health check endpoint for the chat service.
    """
    return {
        "service": "chat",
        "status": "operational",
        "description": "DATACOM-7 chat service is running",
    }
