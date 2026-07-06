"""Agent definitions (reusable config) + runs (instances). A run always
references a definition and never re-creates the agent."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.loop import run_agent
from app.agents.models import AgentDefinition, AgentRun, AgentStatus
from app.agents.schemas import (
    AgentDefinitionCreate,
    AgentDefinitionResponse,
    AgentDefinitionUpdate,
    AgentRunCreate,
    AgentRunResponse,
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


async def _load_run(run_id: int, user_id: int, session: AsyncSession) -> AgentRun:
    row = (await session.execute(select(AgentRun).where(AgentRun.id == run_id))).scalar_one_or_none()
    if row is None or row.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
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


# --- runs -----------------------------------------------------------------


@router.post("/runs", response_model=AgentRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_run(
    body: AgentRunCreate,
    background: BackgroundTasks,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Instantiate a run from a definition and trigger it in the background.

    Creates an AgentRun (status=queued) referencing the definition, then
    schedules run_agent, which opens its own session and drives the loop to
    done/failed. Returns 202 with the queued run; poll GET /runs/{id} for
    status and result_md.
    """
    definition = await _load_definition(body.definition_id, current["id"], session)

    run = AgentRun(
        tenant_id=current["tenant_id"],
        user_id=current["id"],
        definition_id=definition.id,
        project_id=body.project_id if body.project_id is not None else definition.project_id,
        chat_id=body.chat_id,
        status=AgentStatus.queued.value,
        trigger_input=body.trigger_input,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    background.add_task(run_agent, run.id)
    return run


@router.get("/runs", response_model=list[AgentRunResponse])
async def list_runs(
    definition_id: int | None = Query(default=None),
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List the current user's runs, newest first, optionally by definition."""
    stmt = select(AgentRun).where(AgentRun.user_id == current["id"])
    if definition_id is not None:
        stmt = stmt.where(AgentRun.definition_id == definition_id)
    rows = await session.execute(stmt.order_by(AgentRun.created_at.desc()))
    return list(rows.scalars().all())


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_run(run_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Fetch a single run's status + result."""
    return await _load_run(run_id, current["id"], session)
