from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy import false as sql_false
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (Index("idx_projects_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    # Per-project system message, layered on top of the base prompt for chats in
    # this project. NULL = not yet authored.
    system_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)
    inputs_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sql_false(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ProjectRAGSource(Base):
    """Join table — which knowledge bases a project may search."""

    __tablename__ = "project_rag_sources"
    __table_args__ = (
        UniqueConstraint("project_id", "rag_source_id", name="uq_project_rag_source"),
        Index("idx_project_rag_sources_project_id", "project_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    rag_source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenant_rag_sources.id", ondelete="CASCADE"), nullable=False
    )
    enabled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProjectIntegration(Base):
    """Join table — which integrations are visible to a project's chat.

    Exactly one of (integration_id, integration_key) is set per row:
    ``integration_id`` for tenant-wide installs, ``integration_key`` for OAuth
    drivers that have no Integration row. Two partial unique indexes keep each
    kind unique per project.
    """

    __tablename__ = "project_integrations"
    __table_args__ = (
        Index("idx_project_integrations_project_id", "project_id"),
        Index(
            "uq_project_integration_id",
            "project_id",
            "integration_id",
            unique=True,
            sqlite_where=text("integration_id IS NOT NULL"),
            postgresql_where=text("integration_id IS NOT NULL"),
        ),
        Index(
            "uq_project_integration_key",
            "project_id",
            "integration_key",
            unique=True,
            sqlite_where=text("integration_key IS NOT NULL"),
            postgresql_where=text("integration_key IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    integration_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("integrations.id", ondelete="CASCADE"), nullable=True
    )
    integration_key: Mapped[str | None] = mapped_column(String, nullable=True)
    enabled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
