from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DashboardResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    project_id: int
    created_by_user_id: int
    title: str
    description: str | None = None
    tags: list[str] | None = None
    sections: list[str] | None = None
    sample_data: dict | None = None
    skill_name: str
    source_chat_id: int | None = None
    scope: str
    created_at: datetime
    updated_at: datetime


class DashboardCreateSchema(BaseModel):
    project_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    spec: dict = Field(default_factory=dict)
    sample_data: dict | None = None
    sections: list[str] | None = None
    skill_name: str = "chart"
    source_chat_id: int | None = None


class FromArtifactSchema(BaseModel):
    project_id: int
    title: str | None = None


class ArtifactResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    chat_id: int
    message_id: int | None = None
    skill_key: str
    filename: str
    content_type: str
    title: str
    size_bytes: int
    source: str | None = None
    created_at: datetime
