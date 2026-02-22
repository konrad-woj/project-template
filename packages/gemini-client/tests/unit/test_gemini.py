import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from gemini_client import gemini as gemini_module
from gemini_client.gemini import Gemini25Flash


class FakeResponse(SimpleNamespace):
    def __init__(self):
        candidate = SimpleNamespace(finish_reason=SimpleNamespace(value="STOP"))
        super().__init__(text="ok", candidates=[candidate], usage_metadata=None, model_version="v1", parsed=None)


def _make_fake_client(monkeypatch, *, async_delay=0.02):
    """Create and patch gemini.genai.Client to a fake client."""
    original_genai = gemini_module.genai

    class FakeAio:
        def __init__(self):
            async def generate_content(*args, **kwargs):
                if async_delay:
                    await asyncio.sleep(async_delay)
                return FakeResponse()

            self.models = SimpleNamespace(generate_content=AsyncMock(side_effect=generate_content))
            self.aclose = AsyncMock()
            self.client = SimpleNamespace(aclose=AsyncMock())

    class FakeClient:
        def __init__(self, api_key=None):
            self.models = SimpleNamespace(generate_content=lambda *args, **kwargs: FakeResponse())
            self.aio = FakeAio()
            self.close_called = False

        def close(self):
            self.close_called = True

    fake_client_instance = FakeClient()

    monkeypatch.setattr(
        gemini_module,
        "genai",
        SimpleNamespace(
            Client=lambda api_key=None: fake_client_instance,
            errors=getattr(original_genai, "errors", SimpleNamespace()),
        ),
    )

    return fake_client_instance


@pytest.mark.asyncio
async def test_concurrent_requests_do_not_close_aio_per_request(monkeypatch):
    """Ensure concurrent async requests don't close the shared aio client per-request."""
    fake_client = _make_fake_client(monkeypatch, async_delay=0.05)
    client = Gemini25Flash()

    config, contents = client.prepare_request(user_prompt="hi")
    tasks = [
        asyncio.create_task(client.send_request_async_with_retry(contents=contents, config=config)) for _ in range(5)
    ]

    await asyncio.sleep(0.01)
    assert fake_client.aio.aclose.call_count == 0

    await asyncio.gather(*tasks)
    assert fake_client.aio.aclose.call_count == 0

    await client.aclose()
    assert fake_client.aio.aclose.await_count >= 1


@pytest.mark.asyncio
async def test_aclose_idempotent(monkeypatch):
    """Ensure aclose can be called multiple times safely."""
    fake_client = _make_fake_client(monkeypatch, async_delay=0)
    client = Gemini25Flash()

    await asyncio.gather(client.aclose(), client.aclose(), client.aclose())

    assert fake_client.aio.aclose.await_count >= 1
    assert client._aio_closed is True


@pytest.mark.asyncio
async def test_async_context_manager_closes_client(monkeypatch):
    """Test that async context manager properly closes connections."""
    fake_client = _make_fake_client(monkeypatch, async_delay=0)

    async with Gemini25Flash() as client:
        config, contents = client.prepare_request(user_prompt="hi")
        await client.send_request_async(contents=contents, config=config)
        assert fake_client.aio.aclose.await_count == 0

    # After exiting context, aclose should have been called
    assert fake_client.aio.aclose.await_count >= 1


@pytest.mark.asyncio
async def test_cannot_use_closed_client(monkeypatch):
    """Test that using a closed client raises RuntimeError."""
    _make_fake_client(monkeypatch, async_delay=0)
    client = Gemini25Flash()

    await client.aclose()
    assert client._aio_closed is True

    config, contents = client.prepare_request(user_prompt="hi")

    with pytest.raises(RuntimeError, match="Cannot send request: client is closed"):
        await client.send_request_async(contents=contents, config=config)


def test_close_calls_sync_close_only(monkeypatch):
    """Test that close() only closes synchronous resources, not async ones."""
    fake_client = _make_fake_client(monkeypatch, async_delay=0)
    client = Gemini25Flash()

    client.close()

    # Sync close should be called
    assert fake_client.close_called is True
    # Async close should NOT be called
    assert fake_client.aio.aclose.await_count == 0
    # _aio_closed flag should still be False
    assert client._aio_closed is False


def test_query_with_conversation_history(monkeypatch):
    """Test that conversation history parameter works (smoke test)."""
    _make_fake_client(monkeypatch, async_delay=0)
    client = Gemini25Flash()

    # Provide conversation history
    history = [
        {"role": "user", "parts": ["First message"]},
        {"role": "model", "parts": ["First response"]},
    ]

    # Should not crash and should accept history parameter
    response = client.query(user_prompt="Follow-up question", history=history)

    assert response is not None
    assert response["text"] == "ok"


def test_query_without_history_backward_compatible(monkeypatch):
    """Test that query works without history (backward compatibility)."""
    _make_fake_client(monkeypatch, async_delay=0)
    client = Gemini25Flash()

    # Should work without history parameter
    response = client.query(user_prompt="Simple question")

    assert response is not None
    assert response["text"] == "ok"


def test_safety_filters_configurable(monkeypatch):
    """Test that safety filter configuration works."""
    _make_fake_client(monkeypatch, async_delay=0)

    # Test with safety filters disabled (default)
    client_unsafe = Gemini25Flash(disable_safety_filters=True)
    response1 = client_unsafe.query(user_prompt="Test")
    assert response1 is not None

    # Test with safety filters enabled
    client_safe = Gemini25Flash(disable_safety_filters=False)
    response2 = client_safe.query(user_prompt="Test")
    assert response2 is not None


def _make_client_with_error(monkeypatch, error_code: int, is_async: bool = False):
    """Helper to create a client that raises ClientError with given code."""
    import google.genai.errors

    call_count = {"count": 0}

    def create_error():
        return google.genai.errors.ClientError(
            code=error_code, response_json={"error": {"message": f"Error {error_code}", "code": error_code}}
        )

    if is_async:

        async def mock_generate_async(*args, **kwargs):
            call_count["count"] += 1
            raise create_error()

        class FakeAio:
            def __init__(self):
                self.models = SimpleNamespace(generate_content=AsyncMock(side_effect=mock_generate_async))
                self.aclose = AsyncMock()

        class FakeClientAsync:
            def __init__(self, api_key=None):
                self.aio = FakeAio()

        fake_client_class = FakeClientAsync
    else:

        def mock_generate_sync(*args, **kwargs):
            call_count["count"] += 1
            raise create_error()

        class FakeClientSync:
            def __init__(self, api_key=None):
                self.models = SimpleNamespace(generate_content=mock_generate_sync)

        fake_client_class = FakeClientSync

    monkeypatch.setattr(
        gemini_module,
        "genai",
        SimpleNamespace(Client=lambda api_key=None: fake_client_class(), errors=google.genai.errors),
    )

    return call_count


def test_no_retry_codes_respected_sync(monkeypatch):
    """Test that no_retry_codes prevents retries for specified error codes."""
    import google.genai.errors

    call_count = _make_client_with_error(monkeypatch, error_code=400)
    client = Gemini25Flash(no_retry_codes=(400, 401), num_retries=5)
    config, contents = client.prepare_request(user_prompt="test")

    with pytest.raises(google.genai.errors.ClientError):
        client.send_request_with_retry(contents=contents, config=config)

    assert call_count["count"] == 1  # Should not retry


def test_no_retry_codes_allows_retry_sync(monkeypatch):
    """Test that errors not in no_retry_codes are retried."""
    import google.genai.errors

    call_count = _make_client_with_error(monkeypatch, error_code=429)
    client = Gemini25Flash(no_retry_codes=(400, 401), num_retries=3)
    config, contents = client.prepare_request(user_prompt="test")

    with pytest.raises(google.genai.errors.ClientError):
        client.send_request_with_retry(contents=contents, config=config)

    assert call_count["count"] == 3  # Should retry all attempts


def test_custom_no_retry_codes_sync(monkeypatch):
    """Test that custom no_retry_codes are respected."""
    import google.genai.errors

    call_count = _make_client_with_error(monkeypatch, error_code=403)
    client = Gemini25Flash(no_retry_codes=(403, 404), num_retries=5)
    config, contents = client.prepare_request(user_prompt="test")

    with pytest.raises(google.genai.errors.ClientError):
        client.send_request_with_retry(contents=contents, config=config)

    assert call_count["count"] == 1  # Should not retry


@pytest.mark.asyncio
async def test_async_ignores_no_retry_codes(monkeypatch):
    """Test that async version respects no_retry_codes."""
    import google.genai.errors

    call_count = _make_client_with_error(monkeypatch, error_code=400, is_async=True)
    client = Gemini25Flash(no_retry_codes=(400,), num_retries=5)  # 400 in no_retry_codes
    config, contents = client.prepare_request(user_prompt="test")

    with pytest.raises(google.genai.errors.ClientError):
        await client.send_request_async_with_retry(contents=contents, config=config)

    assert call_count["count"] == 1  # Should not retry when code is in no_retry_codes
