"""Document routes: upload, list, folder tree, fetch, and delete."""

import hashlib
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.connection import get_session
from app.documents.chunking import TextSplitterService
from app.documents.indexing import index_document
from app.documents.models import Document, DocumentChunk, DocumentIndexMode, DocumentStatus
from app.documents.processors.registry import DocumentProcessorRegistry, index_mode_for_mimetype
from app.documents.schemas import DocumentListSchema, DocumentSchema, FolderTreeNode
from app.documents.storage import get_storage_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

_registry = DocumentProcessorRegistry()


def _estimate_tokens(text: str) -> int:
    # Rough heuristic — ~4 characters per token — good enough for a stored count.
    return max(1, len(text) // 4)


async def _ingest(document: Document, file_path: str, session: AsyncSession) -> None:
    """Extract text, chunk it, and persist chunks. Sets the document status."""
    processor = _registry.get_processor(document.mimetype)

    # Best-effort metadata from the file itself.
    if hasattr(processor, "extract_metadata"):
        meta = await processor.extract_metadata(file_path)
        document.author = meta.get("author")
        document.doc_title = meta.get("doc_title")
        document.authored_at = meta.get("authored_at")

    if document.index_mode == DocumentIndexMode.stub and hasattr(processor, "extract_stub"):
        stub = await processor.extract_stub(file_path)
        texts = [stub.get("summary", "")]
    else:
        text = await processor.extract_text(file_path)
        texts = await TextSplitterService().split_text(text)

    for i, chunk in enumerate(texts):
        session.add(
            DocumentChunk(
                document_id=document.id,
                chunk_index=i,
                content=chunk,
                token_count=_estimate_tokens(chunk),
            )
        )
    # Push the chunk vectors into the search index (guarded — no-op without
    # embeddings/Qdrant configured).
    await index_document(document.id, texts)
    document.status = DocumentStatus.indexed


@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=DocumentSchema)
async def upload(
    file: UploadFile = File(...),
    folder_path: str | None = Form(default=None),
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload a file, store it, and ingest its text into the knowledge base."""
    mimetype = DocumentProcessorRegistry.resolve_mimetype(file.filename, file.content_type)
    if mimetype is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    document = Document(
        tenant_id=current["tenant_id"],
        user_id=current["id"],
        filename=file.filename or "untitled",
        mimetype=mimetype,
        size=len(data),
        file_hash=hashlib.sha256(data).hexdigest(),
        status=DocumentStatus.processing,
        index_mode=index_mode_for_mimetype(mimetype),
        folder_path=folder_path,
        source="upload",
    )
    session.add(document)
    await session.flush()  # assign document.id

    storage = get_storage_provider()
    file_path = await storage.save_file(document.tenant_id, document.id, data, document.filename)

    try:
        await _ingest(document, file_path, session)
    except Exception as exc:  # noqa: BLE001 — surface ingest failure on the row
        logger.exception("Ingestion failed for document %s", document.id)
        document.status = DocumentStatus.error
        document.error_message = str(exc)

    await session.commit()
    await session.refresh(document)
    return document


@router.get("/", response_model=DocumentListSchema)
async def list_documents(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List documents, most recent first."""
    total = (await session.execute(select(func.count()).select_from(Document))).scalar_one()
    rows = (
        (await session.execute(select(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset)))
        .scalars()
        .all()
    )
    return DocumentListSchema(
        total=total,
        page=(offset // limit) + 1,
        limit=limit,
        documents=[DocumentSchema.model_validate(r) for r in rows],
    )


@router.get("/folders", response_model=list[FolderTreeNode])
async def folders(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Return the virtual folder tree materialized from document folder paths."""
    rows = (
        await session.execute(
            select(Document.folder_path, func.count())
            .where(Document.folder_path.is_not(None))
            .group_by(Document.folder_path)
        )
    ).all()
    return _build_folder_tree(rows)


@router.get("/supported-types")
async def supported_types(current=Depends(get_current_user)):
    """List the MIME types accepted by the upload endpoint."""
    return DocumentProcessorRegistry.get_supported_types()


@router.get("/{document_id}", response_model=DocumentSchema)
async def get_document(
    document_id: int,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Fetch a single document."""
    doc = (await session.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a document and its stored file."""
    doc = (await session.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await get_storage_provider().delete_file(doc.tenant_id, doc.id, doc.filename)
    await session.delete(doc)
    await session.commit()


def _build_folder_tree(rows: list[tuple[str, int]]) -> list[FolderTreeNode]:
    """Build a nested folder tree from (folder_path, count) pairs."""
    nodes: dict[str, FolderTreeNode] = {}
    roots: dict[str, FolderTreeNode] = {}

    for path, count in rows:
        parts = path.split("/")
        accumulated = ""
        parent: FolderTreeNode | None = None
        for depth, part in enumerate(parts):
            accumulated = f"{accumulated}/{part}" if accumulated else part
            node = nodes.get(accumulated)
            if node is None:
                node = FolderTreeNode(name=part, full_path=accumulated, document_count=0, children=[])
                nodes[accumulated] = node
                if parent is None:
                    roots[accumulated] = node
                else:
                    parent.children.append(node)
            # The count attaches to the exact (leaf) path it was recorded under.
            if depth == len(parts) - 1:
                node.document_count += count
            parent = node

    return list(roots.values())
