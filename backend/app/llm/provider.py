"""LLM provider interface and implementations (Anthropic Claude, Alibaba Qwen).

The chat pipeline talks to models exclusively through `LLMProvider`, so adding
another vendor is a new subclass plus a `_PROVIDER_CLASSES` entry — no caller
changes. `create_llm_provider()` resolves the configured provider from settings.
"""

import json
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from app.config import settings


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    # Populated by generate() after each non-streaming call. Callers that want
    # token usage read this after calling generate(). Shape:
    # {"input_tokens": int, "output_tokens": int} or None.
    last_usage: dict | None = None

    # Set by create_llm_provider() — the selection key (e.g. "anthropic").
    provider_key: str = "unknown"

    @abstractmethod
    async def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 16384) -> str:
        """Generate a complete response (non-streaming)."""

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 16384,
    ) -> AsyncGenerator[dict, None]:
        """Stream a response from a message list.

        Yields dicts:
          {"type": "text", "text": "..."}
          {"type": "tool_use", "id": "...", "name": "...", "input": {...}}
          {"type": "end_turn"}
          {"type": "usage", "input_tokens": int, "output_tokens": int}
        """


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.base_url = base_url or settings.ANTHROPIC_BASE_URL
        self.model = model or settings.ANTHROPIC_MODEL
        self._client = None

    @property
    def client(self):
        """Build the SDK client lazily so the provider can be constructed
        without credentials (import/wiring) — only a real call needs the key."""
        if self._client is None:
            from anthropic import AsyncAnthropic

            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = AsyncAnthropic(**kwargs)
        return self._client

    async def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 16384) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        if getattr(response, "usage", None) is not None:
            self.last_usage = {
                "input_tokens": response.usage.input_tokens or 0,
                "output_tokens": response.usage.output_tokens or 0,
            }
        else:
            self.last_usage = None
        return response.content[0].text

    async def generate_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 16384,
    ) -> AsyncGenerator[dict, None]:
        system_message = None
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg.get("content", "")
            else:
                filtered_messages.append(msg)

        kwargs: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": filtered_messages,
        }

        # Mark the system prompt and tool block as ephemerally cacheable.
        # Anthropic caches an exact prefix for ~5 minutes, discounting cached
        # tokens heavily. No behavior change for the caller.
        if system_message:
            kwargs["system"] = [{"type": "text", "text": system_message, "cache_control": {"type": "ephemeral"}}]
        if tools:
            clean_tools = [{k: v for k, v in t.items() if not k.startswith("_")} for t in tools]
            if clean_tools:
                clean_tools[-1] = {**clean_tools[-1], "cache_control": {"type": "ephemeral"}}
            kwargs["tools"] = clean_tools

        async with self.client.messages.stream(**kwargs) as stream:
            async for event in stream:
                # The SDK emits a convenience `text` event per fragment; handle
                # only that to avoid double-emitting the raw delta events.
                if event.type == "text":
                    text_chunk = getattr(event, "text", "") or ""
                    if text_chunk:
                        yield {"type": "text", "text": text_chunk}

            final = await stream.get_final_message()

        for block in final.content:
            if block.type == "tool_use":
                yield {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}

        if final.stop_reason == "end_turn":
            yield {"type": "end_turn"}

        if final.usage is not None:
            yield {
                "type": "usage",
                "input_tokens": final.usage.input_tokens,
                "output_tokens": final.usage.output_tokens,
            }


class AlibabaProvider(LLMProvider):
    """Alibaba Cloud Model Studio (DashScope) provider — OpenAI-compatible, serves Qwen."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        self.base_url = base_url or settings.DASHSCOPE_BASE_URL
        self.model = model or settings.DASHSCOPE_MODEL
        self._client = None

    @property
    def client(self):
        """Build the SDK client lazily so the provider constructs without a key."""
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    async def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 16384) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = getattr(response, "usage", None)
        self.last_usage = (
            {"input_tokens": usage.prompt_tokens or 0, "output_tokens": usage.completion_tokens or 0} if usage else None
        )
        return response.choices[0].message.content

    async def generate_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 16384,
    ) -> AsyncGenerator[dict, None]:
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            kwargs["tools"] = tools

        # Tool-call fragments arrive spread across chunks (by index) and must be
        # accumulated before they can be emitted.
        pending_tools: dict[int, dict] = {}

        stream = await self.client.chat.completions.create(**kwargs)
        async for chunk in stream:
            # The final usage chunk carries usage with an empty choices list.
            if getattr(chunk, "usage", None) is not None:
                yield {
                    "type": "usage",
                    "input_tokens": chunk.usage.prompt_tokens,
                    "output_tokens": chunk.usage.completion_tokens,
                }
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            if getattr(delta, "content", None):
                yield {"type": "text", "text": delta.content}

            for tc in getattr(delta, "tool_calls", None) or []:
                slot = pending_tools.setdefault(tc.index, {"id": None, "name": "", "args": ""})
                if tc.id:
                    slot["id"] = tc.id
                if tc.function and tc.function.name:
                    slot["name"] = tc.function.name
                if tc.function and tc.function.arguments:
                    slot["args"] += tc.function.arguments

            if choice.finish_reason:
                for slot in pending_tools.values():
                    try:
                        parsed = json.loads(slot["args"]) if slot["args"] else {}
                    except json.JSONDecodeError:
                        parsed = {}
                    yield {"type": "tool_use", "id": slot["id"], "name": slot["name"], "input": parsed}
                pending_tools.clear()
                if choice.finish_reason == "stop":
                    yield {"type": "end_turn"}


_PROVIDER_CLASSES: dict[str, type[LLMProvider]] = {
    "anthropic": AnthropicProvider,
    "alibaba": AlibabaProvider,
}


def create_llm_provider(
    provider_key: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> LLMProvider:
    """Create an LLM provider instance from the given key (or settings.LLM_PROVIDER)."""
    key = provider_key or settings.LLM_PROVIDER
    cls = _PROVIDER_CLASSES.get(key)
    if cls is None:
        raise ValueError(f"Unknown LLM provider: {key}")

    kwargs = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    if model:
        kwargs["model"] = model
    instance = cls(**kwargs)
    instance.provider_key = key
    return instance


_llm_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    """Return a process-wide configured provider (built once, then reused)."""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = create_llm_provider()
    return _llm_provider
