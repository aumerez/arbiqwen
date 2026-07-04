"""Agent task schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentTaskResponse(BaseModel):
    id: int
    tenant_id: int
    user_id: int | None
    project_id: int | None
    chat_id: int | None
    title: str
    description: str | None
    task_type: str | None
    prompt_template: str
    steps: list
    allowed_tools: list
    status: str
    execution_side: str
    result_md: str | None
    error: dict | None
    spawn_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentTaskCreate(BaseModel):
    title: str
    description: str | None = None
    task_type: str | None = None
    prompt_template: str
    steps: list = Field(default_factory=list)
    allowed_tools: list = Field(default_factory=list)
    execution_side: str = "backend"
    project_id: int | None = None
    chat_id: int | None = None


class AgentTaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    prompt_template: str | None = None
    steps: list | None = None
    allowed_tools: list | None = None
    status: str | None = None
