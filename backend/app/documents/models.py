from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    DateTime,
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


class DocumentStatus(StrEnum):
    queued = "queued"
    processing = "processing"
    indexed = "indexed"
    error = "error"


class DocumentIndexMode(StrEnum):
    full = "full"  # prose: full text -> chunk -> embed (RAG)
    stub = "stub"  # tabular: discovery summary only
    none = "none"  # external dataset: not indexed


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_user_id", "user_id"),
        Index("idx_documents_status", "status"),
        Index("idx_documents_folder_path", "folder_path"),
        Index("idx_documents_source_external_id", "source", "external_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    mimetype: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256 hex digest
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus, name="document_status", native_enum=False),
        nullable=False,
        default=DocumentStatus.queued,
    )
    # Content-type-aware ingestion mode: prose is chunked + embedded (full),
    # tabular files get a discovery summary only (stub).
    index_mode: Mapped[DocumentIndexMode] = mapped_column(
        SQLEnum(DocumentIndexMode, name="document_index_mode", native_enum=False),
        nullable=False,
        default=DocumentIndexMode.full,
        server_default=DocumentIndexMode.full.value,
    )
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    # Metadata extracted from the document itself — best-effort, may be missing.
    author: Mapped[str | None] = mapped_column(String, nullable=True)
    doc_title: Mapped[str | None] = mapped_column(String, nullable=True)
    authored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Virtual folder path, slash-delimited ("reports/2026"). NULL = root.
    # Folders materialize from existing rows; there is no separate table.
    folder_path: Mapped[str | None] = mapped_column(String, nullable=True)
    # Provider-aware source for documents from outside the upload flow.
    # "upload" (default) / "google_drive" / etc; external_id is the provider file id.
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    external_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (Index("idx_document_chunks_document_id", "document_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
