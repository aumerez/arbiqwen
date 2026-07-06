from datetime import datetime
from enum import StrEnum

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


class AgentStatus(StrEnum):
    """Lifecycle of an agent run."""

    draft = "draft"
    queued = "queued"
    working = "working"
    reporting = "reporting"
    done = "done"
    failed = "failed"


class AgentTrigger(StrEnum):
    """How a run gets instantiated from a definition."""

    manual = "manual"
    webhook = "webhook"


class AgentDefinition(Base):
    """Reusable agent config. A definition is a triggerable unit (like an
    integration) — it holds the prompt, tool allowlist, and model, and never
    carries run state. Runs instantiate FROM it."""

    __tablename__ = "agent_definitions"
    __table_args__ = (Index("idx_agent_definitions_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    # Per-agent tool whitelist — which integrations this definition may call.
    allowed_tools: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Optional model override; null → resolve the tenant/provider default.
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    trigger: Mapped[str] = mapped_column(String, nullable=False, default=AgentTrigger.manual.value)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AgentRun(Base):
    """One execution instance of a definition. Carries all run state
    (status/result/error/timestamps); config is read from the definition via
    `definition_id`. Re-running a definition creates a NEW run — it never
    copies the config into a new agent."""

    __tablename__ = "agent_runs"
    __table_args__ = (Index("idx_agent_runs_definition_created", "definition_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    definition_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agent_definitions.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    chat_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("chats.id", ondelete="SET NULL"), nullable=True)

    status: Mapped[str] = mapped_column(String, nullable=False, default=AgentStatus.draft.value)
    # The input that triggered this run (e.g. the inbound inquiry text).
    trigger_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
