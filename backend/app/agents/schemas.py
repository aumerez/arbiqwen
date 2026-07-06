"""Agent task schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentDefinitionResponse(BaseModel):
    id: int
    tenant_id: int
    user_id: int | None
    project_id: int | None
    name: str
    description: str | None
    prompt_template: str
    allowed_tools: list
    model: str | None
    trigger: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentDefinitionCreate(BaseModel):
    name: str
    description: str | None = None
    prompt_template: str
    allowed_tools: list = Field(default_factory=list)
    model: str | None = None
    trigger: str = "manual"
    project_id: int | None = None


class AgentDefinitionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    prompt_template: str | None = None
    allowed_tools: list | None = None
    model: str | None = None
    trigger: str | None = None


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
