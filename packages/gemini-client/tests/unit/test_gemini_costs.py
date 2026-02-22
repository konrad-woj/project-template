import time
from types import SimpleNamespace

import pytest

from gemini_client.gemini import Gemini25Flash, _compute_costs_from_usage


@pytest.fixture
def model():
    return Gemini25Flash()


class DummyResponse:
    """Minimal fake response shape used by GeminiLLM._process_response."""

    def __init__(self, usage_meta, text="ok", model_version="gemini-2.5-flash"):
        self.text = text
        self.model_version = model_version
        self.parsed = None
        self.usage_metadata = usage_meta
        fr = SimpleNamespace(value="STOP")
        candidate = SimpleNamespace(finish_reason=fr, url_context_metadata=None)
        self.candidates = [candidate]


class DummyUsage:
    """Mimics the SDK usage object."""

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


def test_compute_costs_includes_tool_and_url_tokens(model):
    usage = {
        "prompt_token_count": 100,
        "candidates_token_count": 50,
        "thoughts_token_count": 5,
        "tool_use_prompt_token_count": 10,
        "tool_use_output_token_count": 4,
        "url_context_prompt_token_count": 20,
        "url_context_output_token_count": 2,
    }

    costs = _compute_costs_from_usage(usage, model)

    assert costs["prompt_tokens"] == 100
    assert costs["tool_use_prompt_tokens"] == 10
    assert costs["tool_use_output_tokens"] == 4
    assert costs["url_prompt_tokens"] == 20
    assert costs["url_output_tokens"] == 2
    assert costs["input_tokens"] == 130
    assert costs["output_tokens"] == 61

    expected_input_cost = 130 * model.input_token_cost
    expected_output_cost = 61 * model.output_token_cost
    assert costs["input_cost"] == pytest.approx(expected_input_cost)
    assert costs["output_cost"] == pytest.approx(expected_output_cost)


def test_compute_costs_classifies_ambiguous_url_keys(model):
    usage = {
        "prompt_token_count": 10,
        "candidates_token_count": 4,
        "thoughts_token_count": 1,
        "some_url_prompt_token_count": 6,
        "other_url_candidate_tokens": 2,
        "unlabeled_url_tokens": 3,
    }

    costs = _compute_costs_from_usage(usage, model)

    assert costs["url_prompt_tokens"] == 9
    assert costs["url_output_tokens"] == 2
    assert costs["url_tokens"] == 11
    assert costs["input_tokens"] == 19
    assert costs["output_tokens"] == 7

    expected_input_cost = 19 * model.input_token_cost
    expected_output_cost = 7 * model.output_token_cost
    assert costs["input_cost"] == pytest.approx(expected_input_cost)
    assert costs["output_cost"] == pytest.approx(expected_output_cost)


def test_compute_costs_ambiguous_keys_with_prompt_and_output_terms(model):
    usage = {
        "prompt_token_count": 5,
        "candidates_token_count": 1,
        "thoughts_token_count": 0,
        "url_prompt_and_output_tokens": 7,
    }

    costs = _compute_costs_from_usage(usage, model)

    assert costs["url_prompt_tokens"] == 7
    assert costs["url_output_tokens"] == 0
    assert costs["input_tokens"] == 12
    assert costs["output_tokens"] == 1

    expected_input_cost = 12 * model.input_token_cost
    expected_output_cost = 1 * model.output_token_cost
    assert costs["input_cost"] == pytest.approx(expected_input_cost)
    assert costs["output_cost"] == pytest.approx(expected_output_cost)


def test_process_response_backwards_compatibility_and_totals(model):
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

    out = model._process_response(resp, start_time=time.time() - 0.1)

    assert out["response"] == out["text"] == "ok"
    assert out["raw_response"] is resp
    assert isinstance(out["usage_metadata"], dict)
    assert out["usage_metadata_obj"] is usage_obj

    expected_input = 95
    expected_output = 36
    assert out["input_tokens"] == expected_input
    assert out["output_tokens"] == expected_output
    assert out["total_tokens"] == 131
    assert out["total_token_count"] == 131

    cm = out["cost_metadata"]
    assert cm["input_tokens"] == expected_input
    assert cm["output_tokens"] == expected_output
    assert cm["url_tokens"] == 11


def test_process_response_returns_all_token_fields_and_costs(model):
    usage_obj = DummyUsage(
        prompt_token_count=12,
        candidates_token_count=7,
        thoughts_token_count=2,
        tool_use_prompt_token_count=3,
        tool_use_output_token_count=1,
        url_context_prompt_token_count=5,
        url_context_output_token_count=2,
    )
    resp = DummyResponse(usage_obj)

    out = model._process_response(resp, start_time=time.time() - 0.05)

    assert out["response"] == out["text"] == "ok"
    assert out["raw_response"] is resp

    cm = out["cost_metadata"]
    expected_input = 20
    expected_output = 12
    assert cm["input_tokens"] == expected_input
    assert cm["output_tokens"] == expected_output
    assert cm["url_tokens"] == 7

    assert out["input_tokens"] == expected_input
    assert out["output_tokens"] == expected_output
    assert out["total_tokens"] == 32
    assert out["usage_metadata"]["total_token_count"] == 32


def test_process_response_handles_missing_usage_metadata_gracefully(model):
    resp = DummyResponse(None)

    out = model._process_response(resp, start_time=time.time() - 0.01)

    assert isinstance(out["usage_metadata"], dict)
    assert out["usage_metadata"].get("total_token_count") == 0

    assert out["input_tokens"] == 0
    assert out["output_tokens"] == 0
    assert out["total_tokens"] == 0

    cm = out.get("cost_metadata", {})
    assert cm.get("input_tokens", 0) == 0
    assert cm.get("output_tokens", 0) == 0
    assert cm.get("url_tokens", 0) == 0
