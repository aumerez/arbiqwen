"""Project routes: workspace CRUD."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.connection import get_session
from app.projects.models import Project
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
