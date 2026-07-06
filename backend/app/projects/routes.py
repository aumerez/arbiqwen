"""Project routes: workspace CRUD and per-project source/integration config."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.connection import get_session
from app.projects.models import Project, ProjectIntegration, ProjectRAGSource
from app.projects.schemas import ProjectCreateSchema, ProjectResponseSchema, ProjectUpdateSchema

router = APIRouter(prefix="/projects", tags=["projects"])


async def _load_owned_project(project_id: int, user_id: int, session: AsyncSession) -> Project:
    project = (await session.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if project is None or project.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("", response_model=list[ProjectResponseSchema])
async def list_projects(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """List the current user's projects."""
    rows = await session.execute(
        select(Project).where(Project.user_id == current["id"]).order_by(Project.created_at)
    )
    return list(rows.scalars().all())


@router.post("", response_model=ProjectResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreateSchema,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a project."""
    project = Project(
        tenant_id=current["tenant_id"],
        user_id=current["id"],
        name=body.name,
        description=body.description,
        icon=body.icon,
        inputs_config=body.inputs_config.model_dump() if body.inputs_config else None,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponseSchema)
async def get_project(
    project_id: int,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Fetch a single project."""
    return await _load_owned_project(project_id, current["id"], session)


@router.patch("/{project_id}", response_model=ProjectResponseSchema)
async def update_project(
    project_id: int,
    body: ProjectUpdateSchema,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a project. Unset fields are left unchanged."""
    project = await _load_owned_project(project_id, current["id"], session)
    updates = body.model_dump(exclude_unset=True)
    if "inputs_config" in updates and updates["inputs_config"] is not None:
        updates["inputs_config"] = body.inputs_config.model_dump()
    for field, value in updates.items():
        setattr(project, field, value)
    await session.commit()
    await session.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a project."""
    project = await _load_owned_project(project_id, current["id"], session)
    await session.delete(project)
    await session.commit()


# --- Per-project RAG sources: which knowledge bases this project may search. ---


@router.get("/{project_id}/rag-sources", response_model=list[int])
async def list_project_rag_sources(
    project_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """List the RAG source ids enabled for this project."""
    await _load_owned_project(project_id, current["id"], session)
    rows = await session.execute(
        select(ProjectRAGSource.rag_source_id).where(ProjectRAGSource.project_id == project_id)
    )
    return [r[0] for r in rows.all()]


@router.post("/{project_id}/rag-sources/{source_id}", status_code=status.HTTP_201_CREATED)
async def enable_project_rag_source(
    project_id: int, source_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Enable a RAG source for this project (idempotent)."""
    await _load_owned_project(project_id, current["id"], session)
    existing = (
        await session.execute(
            select(ProjectRAGSource).where(
                ProjectRAGSource.project_id == project_id, ProjectRAGSource.rag_source_id == source_id
            )
        )
    ).scalar_one_or_none()
    if existing:
        return {"status": "already_enabled"}
    session.add(ProjectRAGSource(project_id=project_id, rag_source_id=source_id))
    await session.commit()
    return {"status": "enabled"}


@router.delete("/{project_id}/rag-sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disable_project_rag_source(
    project_id: int, source_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Disable a RAG source for this project."""
    await _load_owned_project(project_id, current["id"], session)
    entry = (
        await session.execute(
            select(ProjectRAGSource).where(
                ProjectRAGSource.project_id == project_id, ProjectRAGSource.rag_source_id == source_id
            )
        )
    ).scalar_one_or_none()
    if entry:
        await session.delete(entry)
        await session.commit()


# --- Per-project integrations: which integrations are visible to this project's chat. ---


@router.get("/{project_id}/integrations-config")
async def list_project_integrations(
    project_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """List integrations enabled for this project.

    Returns ``{integration_ids, integration_keys}``: ids point at tenant-wide
    install rows; keys identify OAuth drivers that have no install row.
    """
    await _load_owned_project(project_id, current["id"], session)
    rows = (
        await session.execute(
            select(ProjectIntegration.integration_id, ProjectIntegration.integration_key).where(
                ProjectIntegration.project_id == project_id
            )
        )
    ).all()
    return {
        "integration_ids": [r[0] for r in rows if r[0] is not None],
        "integration_keys": [r[1] for r in rows if r[1] is not None],
    }


@router.post("/{project_id}/integrations-config/{instance_id}", status_code=status.HTTP_201_CREATED)
async def enable_project_integration(
    project_id: int, instance_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Enable a tenant-wide integration instance for this project (idempotent)."""
    await _load_owned_project(project_id, current["id"], session)
    existing = (
        await session.execute(
            select(ProjectIntegration).where(
                ProjectIntegration.project_id == project_id, ProjectIntegration.integration_id == instance_id
            )
        )
    ).scalar_one_or_none()
    if existing:
        return {"status": "already_enabled"}
    session.add(ProjectIntegration(project_id=project_id, integration_id=instance_id))
    await session.commit()
    return {"status": "enabled"}


@router.delete("/{project_id}/integrations-config/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disable_project_integration(
    project_id: int, instance_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Disable a tenant-wide integration instance for this project."""
    await _load_owned_project(project_id, current["id"], session)
    entry = (
        await session.execute(
            select(ProjectIntegration).where(
                ProjectIntegration.project_id == project_id, ProjectIntegration.integration_id == instance_id
            )
        )
    ).scalar_one_or_none()
    if entry:
        await session.delete(entry)
        await session.commit()


@router.post("/{project_id}/oauth-integrations-config/{key}", status_code=status.HTTP_201_CREATED)
async def enable_project_oauth_integration(
    project_id: int, key: str, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Enable an OAuth integration (by driver key) for this project (idempotent)."""
    await _load_owned_project(project_id, current["id"], session)
    existing = (
        await session.execute(
            select(ProjectIntegration).where(
                ProjectIntegration.project_id == project_id, ProjectIntegration.integration_key == key
            )
        )
    ).scalar_one_or_none()
    if existing:
        return {"status": "already_enabled"}
    session.add(ProjectIntegration(project_id=project_id, integration_key=key))
    await session.commit()
    return {"status": "enabled"}


@router.delete("/{project_id}/oauth-integrations-config/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def disable_project_oauth_integration(
    project_id: int, key: str, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Disable an OAuth integration (by driver key) for this project."""
    await _load_owned_project(project_id, current["id"], session)
    entry = (
        await session.execute(
            select(ProjectIntegration).where(
                ProjectIntegration.project_id == project_id, ProjectIntegration.integration_key == key
            )
        )
    ).scalar_one_or_none()
    if entry:
        await session.delete(entry)
        await session.commit()
