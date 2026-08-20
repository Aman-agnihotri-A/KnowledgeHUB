import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


from app.models.enums import MessageRole


class ConversationCreate(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=255,
    )


class ConversationSummary(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationMessageRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    conversation_id: uuid.UUID
    message_index: int
    role: MessageRole
    content: str
    sources: list[dict] | None
    created_at: datetime
    updated_at: datetime


class ConversationRead(ConversationSummary):
    messages: list[ConversationMessageRead]