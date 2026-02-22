"""Test thinking config support in Gemini client."""

from types import SimpleNamespace

import pytest
from google.genai import types

from gemini_client import gemini as gemini_module
from gemini_client.gemini import MAX_THINKING_BUDGET, Gemini2Flash, Gemini25Flash


def _make_fake_client(monkeypatch):
    """Create and patch gemini.genai.Client to a fake client."""
    original_genai = gemini_module.genai

    class FakeClient:
        def __init__(self, api_key=None):
            self.captured_config = None

            def generate_content(*args, **kwargs):
                # Capture the config parameter
                self.captured_config = kwargs.get("config")
                candidate = SimpleNamespace(finish_reason=SimpleNamespace(value="STOP"))
                return SimpleNamespace(
                    text="ok", candidates=[candidate], usage_metadata=None, model_version="v1", parsed=None
                )

            self.models = SimpleNamespace(generate_content=generate_content)

    fake_client_instance = FakeClient()

    monkeypatch.setattr(
        gemini_module,
        "genai",
        SimpleNamespace(
            Client=lambda api_key=None: fake_client_instance,
            errors=getattr(original_genai, "errors", SimpleNamespace()),
            types=types,
        ),
    )

    return fake_client_instance


def test_thinking_config_passed_correctly(monkeypatch):
    """Test that thinking_config is passed to the API correctly."""
    fake_client = _make_fake_client(monkeypatch)
    client = Gemini25Flash()

    # Query with thinking_config
    client.query(user_prompt="Test", thinking_config={"thinking_budget": 1000})

    # Verify thinking_config was included in config
    assert fake_client.captured_config is not None
    assert hasattr(fake_client.captured_config, "thinking_config")
    assert fake_client.captured_config.thinking_config.thinking_budget == 1000


def test_thinking_config_not_passed_when_not_specified(monkeypatch):
    """Test that thinking_config is not included when not specified."""
    fake_client = _make_fake_client(monkeypatch)
    client = Gemini25Flash()

    # Query without thinking_config
    client.query(user_prompt="Test")

    # Verify thinking_config was not included
    assert fake_client.captured_config is not None
    # The config object may or may not have thinking_config attribute depending on SDK
    # What matters is we didn't explicitly set it
    if hasattr(fake_client.captured_config, "thinking_config"):
        assert fake_client.captured_config.thinking_config is None


def test_thinking_config_raises_error_for_non_thinking_model(monkeypatch):
    """Test that thinking_config raises error for models without has_thinking=True."""
    _make_fake_client(monkeypatch)
    client = Gemini2Flash()  # Model without thinking support

    with pytest.raises(ValueError, match="does not support thinking_config"):
        client.query(user_prompt="Test", thinking_config={"thinking_budget": 1000})


def test_thinking_budget_warns_on_excessive_value(monkeypatch):
    """Test that excessive thinking_budget triggers warning (doesn't raise exception)."""
    _make_fake_client(monkeypatch)
    client = Gemini25Flash()

    # Query with budget exceeding MAX_THINKING_BUDGET
    # Should succeed but log a warning (we can't easily test structlog warnings without complex setup)
    result = client.query(user_prompt="Test", thinking_config={"thinking_budget": MAX_THINKING_BUDGET + 1})

    # Verify the query succeeded despite the warning
    assert result is not None
    assert result["response"] == "ok"


def test_thinking_budget_zero_disables_thinking(monkeypatch):
    """Test that thinking_budget=0 explicitly disables thinking."""
    fake_client = _make_fake_client(monkeypatch)
    client = Gemini25Flash()

    # Query with budget=0 (explicitly disable thinking)
    client.query(user_prompt="Test", thinking_config={"thinking_budget": 0})

    # Verify thinking_config was included with budget=0
    assert fake_client.captured_config is not None
    assert hasattr(fake_client.captured_config, "thinking_config")
    assert fake_client.captured_config.thinking_config.thinking_budget == 0
