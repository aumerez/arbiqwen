"""Dashboard and artifact routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.dashboards.models import Artifact, Dashboard
from app.dashboards.schemas import (
    ArtifactResponseSchema,
    DashboardCreateSchema,
    DashboardResponseSchema,
    FromArtifactSchema,
)
from app.database.connection import get_session

router = APIRouter(prefix="/dashboards", tags=["dashboards"])
artifacts_router = APIRouter(prefix="/artifacts", tags=["artifacts"])


async def _load_dashboard(dashboard_id: int, user_id: int, session: AsyncSession) -> Dashboard:
    dash = (await session.execute(select(Dashboard).where(Dashboard.id == dashboard_id))).scalar_one_or_none()
    if dash is None or dash.created_by_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    return dash


@router.get("", response_model=list[DashboardResponseSchema])
async def list_dashboards(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """List the current user's dashboards."""
    rows = await session.execute(
        select(Dashboard).where(Dashboard.created_by_user_id == current["id"]).order_by(Dashboard.created_at.desc())
    )
    return list(rows.scalars().all())


@router.get("/{dashboard_id}", response_model=DashboardResponseSchema)
async def get_dashboard(
    dashboard_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Fetch a single dashboard."""
    return await _load_dashboard(dashboard_id, current["id"], session)


@router.post("", response_model=DashboardResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    body: DashboardCreateSchema,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a dashboard from a render spec."""
    dash = Dashboard(
        tenant_id=current["tenant_id"],
        created_by_user_id=current["id"],
        project_id=body.project_id,
        title=body.title,
        description=body.description,
        tags=body.tags,
        spec=body.spec,
        sample_data=body.sample_data,
        sections=body.sections,
        skill_name=body.skill_name,
        source_chat_id=body.source_chat_id,
    )
    session.add(dash)
    await session.commit()
    await session.refresh(dash)
    return dash


@router.post("/from-artifact/{artifact_id}", response_model=DashboardResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_from_artifact(
    artifact_id: int,
    body: FromArtifactSchema,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Promote a chat artifact into a saved dashboard."""
    artifact = (await session.execute(select(Artifact).where(Artifact.id == artifact_id))).scalar_one_or_none()
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    dash = Dashboard(
        tenant_id=current["tenant_id"],
        created_by_user_id=current["id"],
        project_id=body.project_id,
        title=body.title or artifact.title,
        spec={"artifact_id": artifact.id, "storage_path": artifact.storage_path},
        skill_name=artifact.skill_key,
        source_chat_id=artifact.chat_id,
    )
    session.add(dash)
    await session.commit()
    await session.refresh(dash)
    return dash


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Delete a dashboard."""
    dash = await _load_dashboard(dashboard_id, current["id"], session)
    await session.delete(dash)
    await session.commit()


@artifacts_router.get("", response_model=list[ArtifactResponseSchema])
async def list_artifacts(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """List artifacts for the current workspace."""
    rows = await session.execute(
        select(Artifact).where(Artifact.tenant_id == current["tenant_id"]).order_by(Artifact.created_at.desc())
    )
    return list(rows.scalars().all())


@artifacts_router.get("/{artifact_id}", response_model=ArtifactResponseSchema)
async def get_artifact(
    artifact_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Fetch a single artifact's metadata."""
    artifact = (await session.execute(select(Artifact).where(Artifact.id == artifact_id))).scalar_one_or_none()
    if artifact is None or artifact.tenant_id != current["tenant_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return artifact
