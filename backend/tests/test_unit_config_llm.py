"""Unit tests for config helpers and the LLM provider factory."""

import pytest

from app.config import Settings
from app.llm import LLMProvider, create_llm_provider


def _settings(**kw):
    # _env_file=None keeps a local .env from leaking into the assertions.
    return Settings(_env_file=None, **kw)


def test_llm_configured_anthropic():
    assert _settings(LLM_PROVIDER="anthropic").llm_configured is False
    assert _settings(LLM_PROVIDER="anthropic", ANTHROPIC_API_KEY="x").llm_configured is True


def test_llm_configured_alibaba():
    assert _settings(LLM_PROVIDER="alibaba").llm_configured is False
    assert _settings(LLM_PROVIDER="alibaba", DASHSCOPE_API_KEY="sk-x").llm_configured is True


def test_llm_configured_unknown_provider():
    assert _settings(LLM_PROVIDER="mystery").llm_configured is False


def test_cors_origins_parsing():
    assert _settings(CORS_ALLOWED_ORIGINS="").cors_origins == []
    assert _settings(CORS_ALLOWED_ORIGINS="http://a, http://b ").cors_origins == ["http://a", "http://b"]


def test_factory_builds_anthropic():
    p = create_llm_provider("anthropic")
    assert type(p).__name__ == "AnthropicProvider"
    assert p.provider_key == "anthropic"
    assert isinstance(p, LLMProvider)


def test_factory_builds_alibaba_qwen():
    p = create_llm_provider("alibaba")
    assert type(p).__name__ == "AlibabaProvider"
    assert p.provider_key == "alibaba"
    assert p.model == "qwen3.7-plus"
    assert "dashscope" in p.base_url


def test_factory_unknown_raises():
    with pytest.raises(ValueError):
        create_llm_provider("nope")
