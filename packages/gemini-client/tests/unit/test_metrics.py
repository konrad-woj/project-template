"""Unit tests for LLM metrics tracking."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from gemini_client.metrics import LLMMetrics, MetricsTrackingWrapper, with_metrics


class TestLLMMetrics:
    """Tests for LLMMetrics class."""

    def test_initial_state(self):
        """Metrics should start at zero."""
        metrics = LLMMetrics(max_concurrent=5)
        assert metrics.total_requests == 0
        assert metrics.in_flight == 0
        assert metrics.active_tasks == 0
        assert metrics.queued_tasks == 0
        assert metrics.pending_tasks == 0
        assert metrics.idle_slots == 5
        assert metrics.max_concurrent == 5

    def test_record_request(self):
        """Recording a request should increment total count and in_flight."""
        metrics = LLMMetrics()
        metrics._record_request_start()
        assert metrics.total_requests == 1
        assert metrics.in_flight == 1
        metrics._record_request_start()
        assert metrics.total_requests == 2
        assert metrics.in_flight == 2

    def test_record_request_end(self):
        """Ending a request should decrement in_flight."""
        metrics = LLMMetrics()
        metrics._record_request_start()
        metrics._record_request_start()
        assert metrics.in_flight == 2
        metrics._record_request_end()
        assert metrics.in_flight == 1
        assert metrics.total_requests == 2  # Total unchanged

    def test_requests_per_minute(self):
        """RPM should count recent requests."""
        metrics = LLMMetrics()
        metrics._record_request_start()
        metrics._record_request_start()
        metrics._record_request_start()
        assert metrics.requests_per_minute == 3

    def test_active_tasks_with_semaphore(self):
        """Active tasks should be derived from semaphore state."""
        semaphore = asyncio.Semaphore(3)
        metrics = LLMMetrics(max_concurrent=3, _semaphore=semaphore)

        # Initially all slots free
        assert metrics.active_tasks == 0
        assert metrics.idle_slots == 3

        # Acquire one permit (simulates one task running)
        semaphore._value = 2  # 1 permit used
        assert metrics.active_tasks == 1
        assert metrics.idle_slots == 2

        # Acquire another permit
        semaphore._value = 1  # 2 permits used
        assert metrics.active_tasks == 2
        assert metrics.idle_slots == 1

    def test_queued_tasks_derived(self):
        """Queued tasks = in_flight - active_tasks."""
        semaphore = asyncio.Semaphore(2)
        metrics = LLMMetrics(max_concurrent=2, _semaphore=semaphore)

        # 5 requests in flight, but only 2 can be active
        metrics._in_flight = 5
        semaphore._value = 0  # Both permits used

        assert metrics.active_tasks == 2
        assert metrics.queued_tasks == 3
        assert metrics.pending_tasks == 5

    def test_snapshot(self):
        """Snapshot should return all metrics as dict."""
        metrics = LLMMetrics(max_concurrent=5)
        metrics._record_request_start()
        snapshot = metrics.snapshot()
        assert snapshot["total_requests"] == 1
        assert snapshot["in_flight"] == 1
        assert snapshot["max_concurrent"] == 5

    def test_str_representation(self):
        """String representation should be readable."""
        metrics = LLMMetrics(max_concurrent=5)
        metrics._record_request_start()
        s = str(metrics)
        assert "total=1" in s
        assert "/5" in s


class TestMetricsTrackingWrapper:
    """Tests for the wrapper that adds metrics to clients."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        client = MagicMock()
        client._semaphore = asyncio.Semaphore(3)
        client.query = MagicMock(return_value={"text": "response"})
        client.query_async = AsyncMock(return_value={"text": "async response"})
        return client

    def test_wraps_client(self, mock_client):
        """Wrapper should delegate to underlying client."""
        wrapper = MetricsTrackingWrapper(mock_client)
        assert wrapper._client is mock_client
        assert wrapper.metrics.max_concurrent == 3

    def test_sync_query_tracking(self, mock_client):
        """Sync query should track metrics."""
        wrapper = MetricsTrackingWrapper(mock_client)
        result = wrapper.query("test prompt")
        assert result == {"text": "response"}
        assert wrapper.metrics.total_requests == 1
        assert wrapper.metrics.in_flight == 0  # Completed
        mock_client.query.assert_called_once_with("test prompt")

    @pytest.mark.asyncio
    async def test_async_query_tracking(self, mock_client):
        """Async query should track metrics."""
        wrapper = MetricsTrackingWrapper(mock_client)

        result = await wrapper.query_async("test prompt")

        assert result == {"text": "async response"}
        assert wrapper.metrics.total_requests == 1
        assert wrapper.metrics.in_flight == 0  # Completed

    @pytest.mark.asyncio
    async def test_concurrent_tracking(self):
        """Multiple concurrent calls should be tracked correctly."""
        # Set up mock with blocking behavior BEFORE wrapping
        call_started = asyncio.Event()
        call_complete = asyncio.Event()

        async def slow_response(*_args, **_kwargs):
            call_started.set()
            await call_complete.wait()
            return {"text": "slow response"}

        mock_client = MagicMock()
        mock_client._semaphore = asyncio.Semaphore(3)
        mock_client.query = MagicMock(return_value={"text": "response"})
        mock_client.query_async = slow_response  # Set before wrapping

        wrapper = MetricsTrackingWrapper(mock_client)

        # Start a task
        task = asyncio.create_task(wrapper.query_async("test"))

        # Wait for it to start
        await call_started.wait()

        # Should have 1 in flight
        assert wrapper.metrics.in_flight == 1
        assert wrapper.metrics.total_requests == 1

        # Complete the task
        call_complete.set()
        await task

        # Should be back to 0
        assert wrapper.metrics.in_flight == 0

    @pytest.mark.asyncio
    async def test_semaphore_state_tracking(self, mock_client):
        """Should track active tasks via semaphore state."""
        wrapper = MetricsTrackingWrapper(mock_client)

        # Manually manipulate semaphore to simulate active tasks
        mock_client._semaphore._value = 1  # 2 permits used out of 3

        # The wrapper should read this state
        assert wrapper.metrics.active_tasks == 2
        assert wrapper.metrics.idle_slots == 1

    def test_attribute_delegation(self, mock_client):
        """Wrapper should delegate unknown attributes to client."""
        mock_client.some_attribute = "test_value"
        wrapper = MetricsTrackingWrapper(mock_client)
        assert wrapper.some_attribute == "test_value"


class TestWithMetrics:
    """Tests for the with_metrics helper function."""

    def test_returns_wrapper(self):
        """with_metrics should return a MetricsTrackingWrapper."""
        client = MagicMock()
        client._semaphore = asyncio.Semaphore(5)
        wrapped = with_metrics(client)
        assert isinstance(wrapped, MetricsTrackingWrapper)
        assert hasattr(wrapped, "metrics")

    def test_preserves_client_interface(self):
        """Wrapped client should have query and query_async methods."""
        client = MagicMock()
        client._semaphore = asyncio.Semaphore(5)
        wrapped = with_metrics(client)
        assert hasattr(wrapped, "query")
        assert hasattr(wrapped, "query_async")
