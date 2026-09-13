"""Domain exceptions, mapped to HTTP responses via `register_exception_handlers`.

Example:
    register_exception_handlers(app)
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from logger import get_logger

log = get_logger(__name__)


class ExampleServiceError(Exception):
    """Base class for domain errors that should be translated into an HTTP response."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NameTooLongError(ExampleServiceError):
    status_code = 422

    def __init__(self, name: str, max_length: int) -> None:
        super().__init__(f"Name {name!r} exceeds the maximum length of {max_length} characters.")
        self.name = name
        self.max_length = max_length


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ExampleServiceError)
    async def _handle_example_service_error(request: Request, exc: ExampleServiceError) -> JSONResponse:
        log.warning("request.rejected", path=request.url.path, error=exc.message)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
