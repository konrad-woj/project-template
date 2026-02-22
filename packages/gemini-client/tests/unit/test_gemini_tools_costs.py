import os

os.environ.setdefault("GEMINI_API_KEY", "test-key-for-unit-tests")

import time
from types import SimpleNamespace

import pytest

from gemini_client.gemini import Gemini25Flash, _compute_costs_from_usage


class DummyResponse:
    def __init__(self, usage_meta, text="ok", model_version="gemini-2.5-flash"):
        self.text = text
        self.model_version = model_version
        self.parsed = None
        self.usage_metadata = usage_meta
        # candidate finish reason
        fr = SimpleNamespace(value="STOP")
        candidate = SimpleNamespace(finish_reason=fr, url_context_metadata=None)
        self.candidates = [candidate]


class DummyUsage:
    def __init__(
        self,
        prompt_token_count=0,
        candidates_token_count=0,
        thoughts_token_count=0,
        tool_use_prompt_token_count=0,
        tool_use_output_token_count=0,
        url_context_prompt_token_count=0,
        url_context_output_token_count=0,
        total_token_count=None,
    ):
        self.prompt_token_count = prompt_token_count
        self.candidates_token_count = candidates_token_count
        self.thoughts_token_count = thoughts_token_count
        self.tool_use_prompt_token_count = tool_use_prompt_token_count
        self.tool_use_output_token_count = tool_use_output_token_count
        self.url_context_prompt_token_count = url_context_prompt_token_count
        self.url_context_output_token_count = url_context_output_token_count
        if total_token_count is not None:
            self.total_token_count = total_token_count


def test_compute_costs_includes_tool_and_url_tokens():
    # Build usage JSON with explicit tool/url token fields
    usage = {
        "prompt_token_count": 100,
        "candidates_token_count": 50,
        "thoughts_token_count": 5,
        "tool_use_prompt_token_count": 10,
        "tool_use_output_token_count": 4,
        "url_context_prompt_token_count": 20,
        "url_context_output_token_count": 2,
    }

    model = Gemini25Flash()
    costs = _compute_costs_from_usage(usage, model)

    assert costs["prompt_tokens"] == 100
    assert costs["tool_use_prompt_tokens"] == 10
    assert costs["tool_use_output_tokens"] == 4
    assert costs["url_prompt_tokens"] == 20
    assert costs["url_output_tokens"] == 2

    # Input tokens = prompt + tool_prompt + url_prompt
    assert costs["input_tokens"] == 100 + 10 + 20
    # Output tokens = candidates + thoughts + tool_output + url_output
    assert costs["output_tokens"] == 50 + 5 + 4 + 2

    # Costs should be computed using model's per-token rates
    expected_input_cost = (100 + 10 + 20) * model.input_token_cost
    expected_output_cost = (50 + 5 + 4 + 2) * model.output_token_cost  # type: ignore[reportOperatorIssue]
    assert pytest.approx(costs["input_cost"], rel=1e-6) == expected_input_cost
    assert pytest.approx(costs["output_cost"], rel=1e-6) == expected_output_cost


def test_process_response_backwards_compatibility_and_totals():
    # Create DummyUsage mimicking SDK object
    usage_obj = DummyUsage(
        prompt_token_count=80,
        candidates_token_count=30,
        thoughts_token_count=2,
        tool_use_prompt_token_count=5,
        tool_use_output_token_count=3,
        url_context_prompt_token_count=10,
        url_context_output_token_count=1,
    )
    resp = DummyResponse(usage_obj)

    model = Gemini25Flash()
    out = model._process_response(resp, start_time=time.time() - 0.1)

    # Backward-compatible aliases
    assert "response" in out
    assert "text" in out
    assert out["response"] == out["text"] == "ok"
    assert "raw_response" in out
    assert out["raw_response"] is resp

    # usage_metadata should be a dict and also keep original object
    assert isinstance(out["usage_metadata"], dict)
    assert "usage_metadata_obj" in out
    assert out["usage_metadata_obj"] is usage_obj

    # total tokens should include url and tool tokens
    expected_input = 80 + 5 + 10
    expected_output = 30 + 2 + 3 + 1
    assert out["input_tokens"] == expected_input
    assert out["output_tokens"] == expected_output
    assert out["total_tokens"] == expected_input + expected_output
    assert out["total_token_count"] == expected_input + expected_output

    # cost metadata present
    assert "cost_metadata" in out
    cm = out["cost_metadata"]
    assert cm["input_tokens"] == expected_input
    assert cm["output_tokens"] == expected_output
    assert "url_tokens" in cm and cm["url_tokens"] == 11


if __name__ == "__main__":
    pytest.main([__file__])
