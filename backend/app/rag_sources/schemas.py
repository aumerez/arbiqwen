"""Pydantic schemas for the RAG source admin API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RAGConfigFieldResponse(BaseModel):
    """A single config field definition from a RAG driver."""

    key: str
    label: str
    field_type: str = "text"
    required: bool = True
    placeholder: str = ""
    help_text: str = ""
    secret: bool = False


class RAGDriverResponse(BaseModel):
    """Info about an installed RAG driver."""

    key: str
    label: str
    description: str
    version: str
    config_schema: list[RAGConfigFieldResponse]


class RAGSourceCreateRequest(BaseModel):
    rag_key: str
    label: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    writable: bool = False


class RAGSourceUpdateRequest(BaseModel):
    label: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    config: dict[str, Any] | None = None
    enabled: bool | None = None
    writable: bool | None = None


class RAGSourceResponse(BaseModel):
    id: int
    tenant_id: int
    rag_key: str
    label: str
    description: str | None = None
    writable: bool
    enabled: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SourceStatsResponse(BaseModel):
    source_id: int
    label: str
    writable: bool
    enabled: bool
    document_count: int | None = None
    chunk_count: int | None = None
    total_size_bytes: int | None = None


class DashboardStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_size_bytes: int
    by_status: dict[str, int]
    by_mimetype: dict[str, int]
    sources: list[SourceStatsResponse]
