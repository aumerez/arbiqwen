"""Agent task routes: definition CRUD surfaced on the workspace home."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentTask
from app.agents.schemas import AgentTaskCreate, AgentTaskResponse, AgentTaskUpdate
from app.auth.dependencies import get_current_user
from app.database.connection import get_session

router = APIRouter(prefix="/api/agents", tags=["agents"])


async def _load(agent_id: int, user_id: int, session: AsyncSession) -> AgentTask:
    agent = (await session.execute(select(AgentTask).where(AgentTask.id == agent_id))).scalar_one_or_none()
    if agent is None or agent.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.get("", response_model=list[AgentTaskResponse])
async def list_agents(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """List the current user's agent tasks, newest first."""
    rows = await session.execute(
        select(AgentTask).where(AgentTask.user_id == current["id"]).order_by(AgentTask.created_at.desc())
    )
    return list(rows.scalars().all())


@router.post("", response_model=AgentTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    body: AgentTaskCreate,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create an agent task definition."""
    agent = AgentTask(
        tenant_id=current["tenant_id"],
        user_id=current["id"],
        **body.model_dump(),
    )
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentTaskResponse)
async def get_agent(agent_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Fetch a single agent task."""
    return await _load(agent_id, current["id"], session)


@router.patch("/{agent_id}", response_model=AgentTaskResponse)
async def update_agent(
    agent_id: int,
    body: AgentTaskUpdate,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update an agent task. Unset fields are left unchanged."""
    agent = await _load(agent_id, current["id"], session)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)
    await session.commit()
    await session.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Delete an agent task."""
    agent = await _load(agent_id, current["id"], session)
    await session.delete(agent)
    await session.commit()
