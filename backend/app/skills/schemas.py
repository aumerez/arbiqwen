"""Pydantic schemas for skill API endpoints."""

from pydantic import BaseModel


class SkillResponse(BaseModel):
    key: str
    name: str
    description: str
    category: str
    icon_name: str
    version: str | None = None
    enabled: bool
    config: dict | None = None


class SkillToggleRequest(BaseModel):
    enabled: bool


class SkillConfigUpdateRequest(BaseModel):
    config: dict
