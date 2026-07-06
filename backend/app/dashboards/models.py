from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Artifact(Base):
    __tablename__ = "artifacts"
    __table_args__ = (Index("idx_artifacts_chat_id", "chat_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    message_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("chat_messages.id", ondelete="SET NULL"), nullable=True
    )
    skill_key: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    # Typed provenance for artifacts produced outside the upload/skill flows
    # (e.g. an integration reader). All nullable.
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    container: Mapped[str | None] = mapped_column(String, nullable=True)
    item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    trust_level: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Dashboard(Base):
    __tablename__ = "dashboards"
    __table_args__ = (
        Index("idx_dashboards_project_id", "project_id"),
        Index("idx_dashboards_created_by_user_id", "created_by_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Opaque render spec — only the rendering skill interprets this.
    spec: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Sample data from the last render, so the edit flow can re-render.
    sample_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Output structure, for browsing without parsing the render.
    sections: Mapped[list | None] = mapped_column(JSON, nullable=True)
    skill_name: Mapped[str] = mapped_column(String, nullable=False)
    source_chat_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("chats.id", ondelete="SET NULL"), nullable=True
    )
    scope: Mapped[str] = mapped_column(String, nullable=False, default="user")  # user, group, company
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
