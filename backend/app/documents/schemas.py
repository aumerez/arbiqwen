from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentSchema(BaseModel):
    id: int
    filename: str
    mimetype: str
    size: int
    status: str
    # Content-type-aware handling mode: "full" (RAG-indexed) / "stub" (tabular)
    # / "none" (not indexed). Drives the documents-list handling badge.
    index_mode: str | None = None
    error_message: str | None = None
    user_id: int | None = None
    # Metadata extracted from the file itself (all best-effort).
    author: str | None = None
    doc_title: str | None = None
    authored_at: datetime | None = None
    # Slash-delimited virtual folder path. Null = root.
    folder_path: str | None = None
    # Provider tracking: "upload" (default) / "google_drive" / etc.
    source: str | None = None
    external_id: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FolderTreeNode(BaseModel):
    """One node in the folder tree returned by GET /documents/folders.

    The tree is materialized from the distinct folder_path values of the
    documents — folders appear when a doc moves in and disappear when the last
    doc moves out. No empty-folder persistence.
    """

    name: str
    full_path: str  # e.g. "reports/audits/2026"
    document_count: int  # immediate count, not recursive
    children: list["FolderTreeNode"] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentListSchema(BaseModel):
    total: int
    page: int
    limit: int
    documents: list[DocumentSchema]
