"""Agent definition CRUD. Runs (instantiate + trigger + history) live below in
feat/agent-model commit 2."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentDefinition
from app.agents.schemas import (
    AgentDefinitionCreate,
    AgentDefinitionResponse,
    AgentDefinitionUpdate,
)
from app.auth.dependencies import get_current_user
from app.database.connection import get_session

router = APIRouter(prefix="/agent", tags=["agents"])


async def _load_definition(definition_id: int, user_id: int, session: AsyncSession) -> AgentDefinition:
    row = (
        await session.execute(select(AgentDefinition).where(AgentDefinition.id == definition_id))
    ).scalar_one_or_none()
    if row is None or row.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent definition not found")
    return row


@router.get("/definitions", response_model=list[AgentDefinitionResponse])
async def list_definitions(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """List the current user's agent definitions, newest first."""
    rows = await session.execute(
        select(AgentDefinition)
        .where(AgentDefinition.user_id == current["id"])
        .order_by(AgentDefinition.created_at.desc())
    )
    return list(rows.scalars().all())


@router.post("/definitions", response_model=AgentDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_definition(
    body: AgentDefinitionCreate,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a reusable agent definition."""
    definition = AgentDefinition(tenant_id=current["tenant_id"], user_id=current["id"], **body.model_dump())
    session.add(definition)
    await session.commit()
    await session.refresh(definition)
    return definition


@router.get("/definitions/{definition_id}", response_model=AgentDefinitionResponse)
async def get_definition(
    definition_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Fetch a single agent definition."""
    return await _load_definition(definition_id, current["id"], session)


@router.patch("/definitions/{definition_id}", response_model=AgentDefinitionResponse)
async def update_definition(
    definition_id: int,
    body: AgentDefinitionUpdate,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update an agent definition. Unset fields are left unchanged."""
    definition = await _load_definition(definition_id, current["id"], session)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(definition, field, value)
    await session.commit()
    await session.refresh(definition)
    return definition


@router.delete("/definitions/{definition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_definition(
    definition_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Delete an agent definition (cascades to its runs)."""
    definition = await _load_definition(definition_id, current["id"], session)
    await session.delete(definition)
    await session.commit()
