"""Pydantic schemas for integration admin endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IntegrationConnectRequest(BaseModel):
    """Connect a new instance — config fields vary per integration."""

    config: dict[str, Any] = Field(default_factory=dict)
    alias: str = Field(..., min_length=1, max_length=255)  # user-provided instance name


class IntegrationUpdateRequest(BaseModel):
    """Update an existing instance. Both fields optional — send only what changed."""

    alias: str | None = Field(default=None, min_length=1, max_length=255)
    config: dict[str, Any] | None = None


class IntegrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    name: str
    instance_alias: str
    description: str | None = None
    type: str
    category: str | None = None
    icon_name: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
