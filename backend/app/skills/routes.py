"""Skill routes: list built-in skills and manage per-workspace enablement."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.connection import get_session
from app.skills.models import TenantSkillConfig
from app.skills.registry import BUILTIN_SKILLS, get_skill
from app.skills.schemas import SkillConfigUpdateRequest, SkillResponse, SkillToggleRequest

router = APIRouter(prefix="/skills", tags=["skills"])


async def _configs(tenant_id: int, session: AsyncSession) -> dict[str, TenantSkillConfig]:
    rows = (
        await session.execute(select(TenantSkillConfig).where(TenantSkillConfig.tenant_id == tenant_id))
    ).scalars().all()
    return {c.skill_key: c for c in rows}


async def _upsert(tenant_id: int, skill_key: str, session: AsyncSession) -> TenantSkillConfig:
    if get_skill(skill_key) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown skill")
    cfg = (
        await session.execute(
            select(TenantSkillConfig).where(
                TenantSkillConfig.tenant_id == tenant_id, TenantSkillConfig.skill_key == skill_key
            )
        )
    ).scalar_one_or_none()
    if cfg is None:
        cfg = TenantSkillConfig(tenant_id=tenant_id, skill_key=skill_key)
        session.add(cfg)
    return cfg


@router.get("", response_model=list[SkillResponse])
async def list_skills(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """List built-in skills merged with this workspace's enablement/config."""
    configs = await _configs(current["tenant_id"], session)
    result = []
    for skill in BUILTIN_SKILLS:
        cfg = configs.get(skill["key"])
        result.append(
            SkillResponse(
                **skill,
                enabled=cfg.enabled if cfg else True,
                config=cfg.config if cfg else None,
            )
        )
    return result


@router.put("/{skill_key}/toggle", response_model=SkillResponse)
async def toggle_skill(
    skill_key: str,
    body: SkillToggleRequest,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Enable or disable a skill for the workspace."""
    cfg = await _upsert(current["tenant_id"], skill_key, session)
    cfg.enabled = body.enabled
    await session.commit()
    return SkillResponse(**get_skill(skill_key), enabled=cfg.enabled, config=cfg.config)


@router.put("/{skill_key}/config", response_model=SkillResponse)
async def update_skill_config(
    skill_key: str,
    body: SkillConfigUpdateRequest,
    current=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a skill's configuration for the workspace."""
    cfg = await _upsert(current["tenant_id"], skill_key, session)
    cfg.config = body.config
    await session.commit()
    return SkillResponse(**get_skill(skill_key), enabled=cfg.enabled, config=cfg.config)
