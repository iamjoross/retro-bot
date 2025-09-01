from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.shared.models import Message, BaseDocument


class Conversation(BaseDocument):
    title: Optional[str] = Field(None, max_length=100, description="Conversation title")
    messages: List[Message] = Field(
        default_factory=list,
        description="Messages in conversation",
    )

    def get_message_count(self) -> int:
        return len(self.messages)

    def get_latest_message(self) -> Optional[Message]:
        return self.messages[-1] if self.messages else None

    def add_message(self, message: Message) -> None:
        self.messages.append(message)
        self.update_timestamp()


class ConversationSummary(BaseModel):
    id: str = Field(..., description="Conversation ID")
    title: Optional[str] = Field(None, description="Conversation title")
    message_count: int = Field(..., description="Number of messages")
    last_message_preview: Optional[str] = Field(
        None, max_length=100, description="Preview of last message"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}


class ConversationListRequest(BaseModel):
    skip: int = Field(0, ge=0, description="Number of conversations to skip")
    limit: int = Field(20, ge=1, le=100, description="Maximum conversations to return")
    include_messages: bool = Field(False, description="Include full message content")


class ConversationUpdateRequest(BaseModel):
    title: Optional[str] = Field(
        None, min_length=1, max_length=100, description="New conversation title"
    )
