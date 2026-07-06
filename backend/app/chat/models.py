from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ChatRole(StrEnum):
    user = "user"
    assistant = "assistant"


class Chat(Base):
    __tablename__ = "chats"
    __table_args__ = (Index("idx_chats_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="chat", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (Index("idx_chat_messages_chat_id", "chat_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Client- or server-generated UUID; an idempotency key so retries don't duplicate rows.
    msg_uuid: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[ChatRole] = mapped_column(SQLEnum(ChatRole, name="chat_role", native_enum=False), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    retrieved_chunk_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    artifacts: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Tool-call cards shown in the UI — local render scope, not sent to the LLM
    # in history. Persisted so the cards survive reload / chat switch.
    tool_calls: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
