"""Agent task schemas."""

from datetime import datetime
from typing import Literal

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


# --- Run-step primitives --------------------------------------------------
# One `run_step` call = one LLM round. The loop (loop.py) owns iteration; these
# types are the wire between the loop, the runner, and the LLM provider. The
# assistant `content` uses the Anthropic-native block shape (a str for a plain
# text turn, or a list of {type: text|tool_use|tool_result} blocks) so tool
# rounds round-trip through the provider unchanged.


class RunStepMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[dict] | None = None


class RunStepToolCall(BaseModel):
    id: str
    name: str
    arguments: dict = Field(default_factory=dict)


class RunStepUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    # Sourced from the provider (provider_key/model), not the usage event.
    provider_key: str | None = None
    model_id: str | None = None


class RunStepRequest(BaseModel):
    messages: list[RunStepMessage]
    # Optional per-round narrowing of the agent's stored allowed_tools. Callers
    # can only narrow, never widen — enforced in the runner.
    allowed_tools: list[str] | None = None


class RunStepResponse(BaseModel):
    next_action: Literal["tool_use", "text", "done"]
    assistant_message: RunStepMessage
    tool_calls: list[RunStepToolCall] = Field(default_factory=list)
    usage: RunStepUsage = Field(default_factory=RunStepUsage)
