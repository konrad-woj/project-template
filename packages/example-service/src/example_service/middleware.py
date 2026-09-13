"""ASGI middleware for request-scoped structured logging context.

Example:
    app.add_middleware(RequestContextMiddleware)
"""

import time
import uuid

import structlog
from fastapi import Request
from logger import get_logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

log = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Binds a request ID into structlog context so every log line in the request carries it."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000
            log.info(
                "request.completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            structlog.contextvars.clear_contextvars()
