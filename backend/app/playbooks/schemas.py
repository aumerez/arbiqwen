from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlaybookStepSchema(BaseModel):
    id: str
    order: int
    type: str  # action, condition, notification, approval
    name: str
    description: str = ""
    config: dict = Field(default_factory=dict)


class PlaybookCreateSchema(BaseModel):
    project_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    icon: str = "Zap"
    status: str = "draft"
    trigger: str = "manual"
    steps: list[PlaybookStepSchema] = Field(default_factory=list)
    scope: str = "user"
    tags: list[str] = Field(default_factory=list)


class PlaybookUpdateSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    icon: str | None = None
    status: str | None = None
    trigger: str | None = None
    steps: list[PlaybookStepSchema] | None = None
    scope: str | None = None
    tags: list[str] | None = None


class PlaybookRunResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    playbook_id: int
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    triggered_by: str | None = None
    steps_completed: int = 0
    steps_total: int = 0
    error: str | None = None


class PlaybookResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    project_id: int
    created_by_user_id: int
    name: str
    description: str | None = None
    icon: str | None = None
    status: str
    trigger: str
    steps: list[dict] | None = None
    scope: str
    tags: list[str] | None = None
    source_chat_id: int | None = None
    created_at: datetime
    updated_at: datetime
