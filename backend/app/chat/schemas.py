"""Chat-related Pydantic schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatCreateSchema(BaseModel):
    """Create a new chat."""

    title: str | None = None


class ChatResponseSchema(BaseModel):
    """Chat metadata."""

    id: int
    user_id: int
    tenant_id: int
    title: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatMessageSchema(BaseModel):
    """A single chat message."""

    id: int
    chat_id: int
    role: str  # "user" or "assistant"
    content: str
    citations: list | None = None
    confidence: float | None = None
    artifacts: list | None = None
    tool_calls: list | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreateSchema(BaseModel):
    """Send a message to a chat."""

    message: str


class TitleGenerationSchema(BaseModel):
    message: str


class TitleResponseSchema(BaseModel):
    title: str
