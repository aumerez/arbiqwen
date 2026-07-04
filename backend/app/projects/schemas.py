"""Project-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationConfigSchema(BaseModel):
    email_on_ticket_create: bool = False
    recipient_emails: list[str] = []


class InputsConfigSchema(BaseModel):
    apis: list[int] = []
    databases: list[str] = []
    notifications: NotificationConfigSchema | None = None


class ProjectCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    icon: str | None = None
    inputs_config: InputsConfigSchema | None = None


class ProjectUpdateSchema(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    icon: str | None = None
    inputs_config: InputsConfigSchema | None = None
    system_message: str | None = Field(None, max_length=20000)


class ProjectResponseSchema(BaseModel):
    id: int
    tenant_id: int
    user_id: int
    name: str
    description: str | None = None
    icon: str | None = None
    inputs_config: InputsConfigSchema | None = None
    is_default: bool
    system_message: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
