from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TenantRAGSource(Base):
    __tablename__ = "tenant_rag_sources"
    __table_args__ = (
        UniqueConstraint("tenant_id", "label", name="uq_tenant_rag_label"),
        Index("idx_tenant_rag_sources_rag_key", "rag_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    rag_key: Mapped[str] = mapped_column(String, nullable=False)  # driver key
    label: Mapped[str] = mapped_column(String, nullable=False)  # human-readable name
    description: Mapped[str | None] = mapped_column(Text, nullable=True)  # context for source selection
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # provider-specific config
    writable: Mapped[bool] = mapped_column(Boolean, default=False)  # can documents be upserted?
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
