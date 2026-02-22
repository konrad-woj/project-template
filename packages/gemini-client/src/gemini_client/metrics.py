"""Real-time metrics tracking for LLM clients.

Provides decorators and utilities to monitor request counts, rates, and concurrency.

Usage
-----

1. Wrap an existing client instance:

    from gemini_client.gemini import Gemini25Flash
    from gemini_client.metrics import with_metrics

    client = Gemini25Flash(max_concurrent_calls=5)
    tracked_client = with_metrics(client)

    # Use as normal
    response = await tracked_client.query_async("Hello")

    # Access metrics
    print(tracked_client.metrics.total_requests)
    print(tracked_client.metrics.requests_per_minute)
    print(tracked_client.metrics.pending_tasks)

2. Real-time monitoring in terminal:

    from gemini_client.metrics import with_metrics, start_metrics_display

    client = with_metrics(Gemini25Flash(max_concurrent_calls=5))

    # Start background display (updates every second)
    stop_display = start_metrics_display(client.metrics)

    # ... run your async tasks ...

    stop_display()  # Stop when done
"""

import asyncio
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class LLMMetrics:
    """Thread-safe metrics collector for LLM request tracking.

    Attributes:
        total_requests: Total number of requests since metrics started.
        requests_per_minute: Requests in the last 60 seconds (sliding window).
        active_tasks: Number of tasks currently executing (holding semaphore).
        queued_tasks: Number of tasks waiting for semaphore.
        max_concurrent: Maximum concurrent calls allowed by the client.
    """

    max_concurrent: int = 10
    _semaphore: asyncio.Semaphore | None = field(default=None, repr=False)
    _total_requests: int = field(default=0, repr=False)
    _in_flight: int = field(default=0, repr=False)
    _request_timestamps: deque = field(default_factory=lambda: deque(maxlen=10000), repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @property
    def total_requests(self) -> int:
        """Total requests since tracking started."""
        return self._total_requests

    @property
    def in_flight(self) -> int:
        """Total tasks in flight (submitted but not completed)."""
        return self._in_flight

    @property
    def active_tasks(self) -> int:
        """Tasks currently executing (holding semaphore).

        Derived from semaphore state: max_concurrent - available_permits.
        """
        if self._semaphore is None:
            return self._in_flight
        # _value is the number of available permits
        available = self._semaphore._value
        return self.max_concurrent - available

    @property
    def queued_tasks(self) -> int:
        """Tasks waiting to acquire semaphore.

        Derived from: in_flight - active_tasks.
        """
        return max(0, self._in_flight - self.active_tasks)

    @property
    def pending_tasks(self) -> int:
        """Total pending tasks (same as in_flight)."""
        return self._in_flight

    @property
    def idle_slots(self) -> int:
        """Available semaphore slots."""
        if self._semaphore is None:
            return max(0, self.max_concurrent - self._in_flight)
        return self._semaphore._value

    @property
    def requests_per_minute(self) -> float:
        """Requests in the last 60 seconds."""
        with self._lock:
            now = time.time()
            cutoff = now - 60.0
            # Remove old timestamps
            while self._request_timestamps and self._request_timestamps[0] < cutoff:
                self._request_timestamps.popleft()
            return len(self._request_timestamps)

    def _record_request_start(self) -> None:
        """Record a new request starting."""
        with self._lock:
            self._total_requests += 1
            self._in_flight += 1
            self._request_timestamps.append(time.time())

    def _record_request_end(self) -> None:
        """Record a request completing."""
        with self._lock:
            self._in_flight = max(0, self._in_flight - 1)

    def snapshot(self) -> dict[str, Any]:
        """Get a snapshot of all metrics."""
        return {
            "total_requests": self.total_requests,
            "requests_per_minute": self.requests_per_minute,
            "in_flight": self.in_flight,
            "active_tasks": self.active_tasks,
            "queued_tasks": self.queued_tasks,
            "idle_slots": self.idle_slots,
            "max_concurrent": self.max_concurrent,
        }

    def __str__(self) -> str:
        return (
            f"total={self.total_requests} | "
            f"rpm={self.requests_per_minute:.1f} | "
            f"active={self.active_tasks}/{self.max_concurrent} | "
            f"queued={self.queued_tasks}"
        )


class MetricsTrackingWrapper:
    """Wrapper that adds metrics tracking to an LLM client.

    Intercepts query_async calls to track request counts and concurrency.
    Monitors the client's semaphore state without interfering with it.
    Preserves all other attributes and methods of the wrapped client.
    """

    def __init__(self, client: Any):
        self._client = client
        semaphore = getattr(client, "_semaphore", None)
        if semaphore is not None:
            max_concurrent = semaphore._value
        else:
            max_concurrent = 10
        self.metrics = LLMMetrics(max_concurrent=max_concurrent, _semaphore=semaphore)
        self._original_query_async = client.query_async
        self._original_query = client.query

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to wrapped client."""
        return getattr(self._client, name)

    def query(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Tracked synchronous query."""
        self.metrics._record_request_start()
        try:
            return self._original_query(*args, **kwargs)
        finally:
            self.metrics._record_request_end()

    async def query_async(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Tracked asynchronous query - monitors but doesn't interfere with semaphore."""
        self.metrics._record_request_start()
        try:
            return await self._original_query_async(*args, **kwargs)
        finally:
            self.metrics._record_request_end()


def with_metrics[T](client: T) -> T:
    """Wrap an LLM client with metrics tracking.

    Args:
        client: An LLM client instance (e.g., Gemini25Flash)

    Returns:
        A wrapped client with a `.metrics` attribute for accessing stats.

    Example:
        client = with_metrics(Gemini25Flash(max_concurrent_calls=5))
        await client.query_async("Hello")
        print(client.metrics.total_requests)  # 1
    """
    return MetricsTrackingWrapper(client)  # type: ignore[return-value]


def start_metrics_display(
    metrics: LLMMetrics,
    interval: float = 1.0,
    output: Callable[[str], None] | None = None,
) -> Callable[[], None]:
    """Start a background thread that displays metrics in real-time.

    Args:
        metrics: The LLMMetrics instance to monitor.
        interval: Update interval in seconds (default 1.0).
        output: Optional custom output function (default: print with carriage return).

    Returns:
        A stop function to call when done monitoring.

    Example:
        stop = start_metrics_display(client.metrics)
        # ... run tasks ...
        stop()
    """
    stop_event = threading.Event()

    def _default_output(text: str) -> None:
        print(f"\r{text}", end="", flush=True)

    output_fn = output or _default_output

    def _display_loop() -> None:
        while not stop_event.is_set():
            output_fn(str(metrics))
            time.sleep(interval)
        # Final newline
        if output is None:
            print()

    thread = threading.Thread(target=_display_loop, daemon=True)
    thread.start()

    def stop() -> None:
        stop_event.set()
        thread.join(timeout=interval * 2)

    return stop


async def start_metrics_display_async(
    metrics: LLMMetrics,
    interval: float = 1.0,
    output: Callable[[str], None] | None = None,
) -> Callable[[], None]:
    """Start an async task that displays metrics in real-time.

    Args:
        metrics: The LLMMetrics instance to monitor.
        interval: Update interval in seconds (default 1.0).
        output: Optional custom output function (default: print with carriage return).

    Returns:
        A stop function to call when done monitoring.
    """
    stop_event = asyncio.Event()

    def _default_output(text: str) -> None:
        print(f"\r{text}", end="", flush=True)

    output_fn = output or _default_output

    async def _display_loop() -> None:
        while not stop_event.is_set():
            output_fn(str(metrics))
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except TimeoutError:
                pass
        if output is None:
            print()

    _task = asyncio.create_task(_display_loop())

    def stop() -> None:
        stop_event.set()
        _task.cancel()

    return stop
