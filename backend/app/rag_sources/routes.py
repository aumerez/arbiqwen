"""RAG source admin routes: drivers, sources CRUD, and dashboard stats."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.connection import get_session
from app.documents.models import Document, DocumentChunk
from app.rag_sources.models import TenantRAGSource
from app.rag_sources.schemas import (
    DashboardStatsResponse,
    RAGConfigFieldResponse,
    RAGDriverResponse,
    RAGSourceCreateRequest,
    RAGSourceResponse,
    RAGSourceUpdateRequest,
)

router = APIRouter(prefix="/api/rag-sources", tags=["rag-sources"])

# Installed drivers. Qdrant is the built-in vector store; the config schema
# drives the "add source" form on the client.
_DRIVERS: list[RAGDriverResponse] = [
    RAGDriverResponse(
        key="qdrant",
        label="Qdrant",
        description="Qdrant vector database.",
        version="1.0",
        config_schema=[
            RAGConfigFieldResponse(key="url", label="URL", placeholder="http://localhost:6333"),
            RAGConfigFieldResponse(key="api_key", label="API Key", required=False, secret=True),
            RAGConfigFieldResponse(key="collection", label="Collection", placeholder="documents"),
        ],
    )
]
_DRIVER_KEYS = {d.key for d in _DRIVERS}


@router.get("/drivers", response_model=list[RAGDriverResponse])
async def list_drivers(current=Depends(get_current_user)):
    """List installed RAG drivers and their config schemas."""
    return _DRIVERS


@router.get("/stats", response_model=DashboardStatsResponse)
async def stats(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Aggregate document/chunk statistics for the RAG dashboard."""
    total_documents = (await session.execute(select(func.count()).select_from(Document))).scalar_one()
    total_chunks = (await session.execute(select(func.count()).select_from(DocumentChunk))).scalar_one()
    total_size = (await session.execute(select(func.coalesce(func.sum(Document.size), 0)))).scalar_one()

    by_status = dict(
        (await session.execute(select(Document.status, func.count()).group_by(Document.status))).all()
    )
    by_mimetype = dict(
        (await session.execute(select(Document.mimetype, func.count()).group_by(Document.mimetype))).all()
    )
    return DashboardStatsResponse(
        total_documents=total_documents,
        total_chunks=total_chunks,
        total_size_bytes=int(total_size),
        by_status={str(k): v for k, v in by_status.items()},
        by_mimetype={str(k): v for k, v in by_mimetype.items()},
        sources=[],
    )


@router.get("", response_model=list[RAGSourceResponse])
async def list_sources(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """List configured RAG sources."""
    rows = (await session.execute(select(TenantRAGSource).order_by(TenantRAGSource.id))).scalars().all()
    return list(rows)


@router.post("", response_model=RAGSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    body: RAGSourceCreateRequest,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add a RAG source."""
    if body.rag_key not in _DRIVER_KEYS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown driver: {body.rag_key}")
    source = TenantRAGSource(
        tenant_id=current["tenant_id"],
        rag_key=body.rag_key,
        label=body.label,
        description=body.description,
        config=body.config,
        writable=body.writable,
    )
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return source


@router.patch("/{source_id}", response_model=RAGSourceResponse)
async def update_source(
    source_id: int,
    body: RAGSourceUpdateRequest,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a RAG source."""
    source = (
        await session.execute(select(TenantRAGSource).where(TenantRAGSource.id == source_id))
    ).scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    await session.commit()
    await session.refresh(source)
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: int,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a RAG source."""
    source = (
        await session.execute(select(TenantRAGSource).where(TenantRAGSource.id == source_id))
    ).scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    await session.delete(source)
    await session.commit()
