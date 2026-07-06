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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Playbook(Base):
    __tablename__ = "playbooks"
    __table_args__ = (Index("idx_playbooks_project_id", "project_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")  # draft, active, archived
    trigger: Mapped[str] = mapped_column(String, nullable=False, default="manual")  # manual, alert, schedule, webhook
    steps: Mapped[list | None] = mapped_column(JSON, nullable=True)  # ordered step objects
    scope: Mapped[str] = mapped_column(String, nullable=False, default="user")  # user, group, company
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    source_chat_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("chats.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    runs: Mapped[list["PlaybookRun"]] = relationship(
        "PlaybookRun", back_populates="playbook", cascade="all, delete-orphan"
    )


class PlaybookRun(Base):
    __tablename__ = "playbook_runs"
    __table_args__ = (Index("idx_playbook_runs_playbook_id", "playbook_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    playbook_id: Mapped[int] = mapped_column(Integer, ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="running")  # running, completed, failed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triggered_by: Mapped[str | None] = mapped_column(String, nullable=True)
    steps_completed: Mapped[int] = mapped_column(Integer, default=0)
    steps_total: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    playbook: Mapped["Playbook"] = relationship("Playbook", back_populates="runs")
