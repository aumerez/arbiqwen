"""Integration routes: marketplace catalog and installed-instance management."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.connection import get_session
from app.integrations.marketplace import get_tile, list_marketplace_tiles
from app.integrations.models import Integration, IntegrationConnection
from app.integrations.schemas import (
    IntegrationConnectRequest,
    IntegrationResponse,
    IntegrationUpdateRequest,
)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
# The desktop reads the catalog from a top-level path, separate from the
# tenant-scoped instance endpoints under /api/integrations.
config_router = APIRouter(tags=["integrations"])


async def _load_instance(instance_id: int, tenant_id: int, session: AsyncSession) -> Integration:
    inst = (await session.execute(select(Integration).where(Integration.id == instance_id))).scalar_one_or_none()
    if inst is None or inst.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    return inst


@router.get("/")
async def list_integrations(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """List the workspace's connected integration instances."""
    rows = (
        (
            await session.execute(
                select(Integration).where(Integration.tenant_id == current["tenant_id"]).order_by(Integration.id)
            )
        )
        .scalars()
        .all()
    )
    return {"drivers": [], "instances": [IntegrationResponse.model_validate(r).model_dump() for r in rows]}


@router.get("/marketplace")
async def marketplace(current=Depends(get_current_user)):
    """Return the installable integration catalog."""
    return {"tiles": list_marketplace_tiles()}


@router.post("/{key}/connect", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def connect(
    key: str,
    body: IntegrationConnectRequest,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Connect a new instance of a marketplace integration."""
    tile = get_tile(key)
    if tile is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown integration: {key}")

    integration = Integration(
        tenant_id=current["tenant_id"],
        name=tile["name"],
        instance_alias=body.alias,
        description=tile["description"],
        type=tile["auth_type"],
        category=tile["key"],
        icon_name=tile["icon_name"],
        status="connected",
        config=body.config or None,
    )
    session.add(integration)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="An integration with this name already exists"
        ) from exc
    session.add(
        IntegrationConnection(integration_id=integration.id, status="connected", connected_at=datetime.now(UTC))
    )
    await session.commit()
    await session.refresh(integration)
    return integration


@router.get("/instances/{instance_id}", response_model=IntegrationResponse)
async def get_instance(
    instance_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Fetch a single connected instance."""
    return await _load_instance(instance_id, current["tenant_id"], session)


@router.put("/instances/{instance_id}", response_model=IntegrationResponse)
async def update_instance(
    instance_id: int,
    body: IntegrationUpdateRequest,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Rename or reconfigure an instance."""
    inst = await _load_instance(instance_id, current["tenant_id"], session)
    if body.alias is not None:
        inst.instance_alias = body.alias
    if body.config is not None:
        inst.config = body.config
    await session.commit()
    await session.refresh(inst)
    return inst


@router.delete("/instances/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_instance(
    instance_id: int, current=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    """Remove a connected instance."""
    inst = await _load_instance(instance_id, current["tenant_id"], session)
    await session.delete(inst)
    await session.commit()


@config_router.get("/integrations-config")
async def integrations_config(current=Depends(get_current_user)):
    """Return the catalog grouped for the settings view."""
    tiles = list_marketplace_tiles()
    categories = sorted({t["category"] for t in tiles})
    return {"tiles": tiles, "categories": categories}
