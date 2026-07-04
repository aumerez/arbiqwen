"""Playbook routes: CRUD and manual run."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.connection import get_session
from app.playbooks.models import Playbook, PlaybookRun
from app.playbooks.schemas import (
    PlaybookCreateSchema,
    PlaybookResponseSchema,
    PlaybookRunResponseSchema,
    PlaybookUpdateSchema,
)

router = APIRouter(prefix="/playbooks", tags=["playbooks"])


async def _load(playbook_id: int, user_id: int, session: AsyncSession) -> Playbook:
    pb = (await session.execute(select(Playbook).where(Playbook.id == playbook_id))).scalar_one_or_none()
    if pb is None or pb.created_by_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
    return pb


@router.get("", response_model=list[PlaybookResponseSchema])
async def list_playbooks(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """List the current user's playbooks."""
    rows = await session.execute(
        select(Playbook).where(Playbook.created_by_user_id == current["id"]).order_by(Playbook.created_at.desc())
    )
    return list(rows.scalars().all())


@router.get("/{playbook_id}", response_model=PlaybookResponseSchema)
async def get_playbook(
    playbook_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Fetch a single playbook."""
    return await _load(playbook_id, current["id"], session)


@router.post("", response_model=PlaybookResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_playbook(
    body: PlaybookCreateSchema,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a playbook."""
    pb = Playbook(
        tenant_id=current["tenant_id"],
        created_by_user_id=current["id"],
        project_id=body.project_id,
        name=body.name,
        description=body.description,
        icon=body.icon,
        status=body.status,
        trigger=body.trigger,
        steps=[s.model_dump() for s in body.steps],
        scope=body.scope,
        tags=body.tags,
    )
    session.add(pb)
    await session.commit()
    await session.refresh(pb)
    return pb


@router.patch("/{playbook_id}", response_model=PlaybookResponseSchema)
async def update_playbook(
    playbook_id: int,
    body: PlaybookUpdateSchema,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a playbook. Unset fields are left unchanged."""
    pb = await _load(playbook_id, current["id"], session)
    updates = body.model_dump(exclude_unset=True)
    if "steps" in updates and updates["steps"] is not None:
        updates["steps"] = [s.model_dump() for s in body.steps]
    for field, value in updates.items():
        setattr(pb, field, value)
    await session.commit()
    await session.refresh(pb)
    return pb


@router.delete("/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playbook(
    playbook_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Delete a playbook."""
    pb = await _load(playbook_id, current["id"], session)
    await session.delete(pb)
    await session.commit()


@router.post("/{playbook_id}/run", response_model=PlaybookRunResponseSchema)
async def run_playbook(
    playbook_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Record a manual run of a playbook's steps."""
    pb = await _load(playbook_id, current["id"], session)
    total = len(pb.steps or [])
    run = PlaybookRun(
        playbook_id=pb.id,
        tenant_id=pb.tenant_id,
        status="completed",
        finished_at=datetime.now(UTC),
        triggered_by="user:manual",
        steps_completed=total,
        steps_total=total,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run
