from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ..., min_length=1, max_length=2000, description="User message to send"
    )
    conversation_id: Optional[str] = Field(
        None, description="ID of existing conversation, or None for new"
    )


class ChatResponse(BaseModel):
    message: str = Field(..., description="DATACOM-7's response message")
    conversation_id: str = Field(..., description="ID of the conversation")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}


class ChatContext(BaseModel):
    user_message: str
    conversation_id: Optional[str] = None
    system_prompt: str
    message_history: list = Field(default_factory=list)
    max_context_messages: int = 4
