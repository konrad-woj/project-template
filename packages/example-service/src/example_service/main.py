import argparse

import uvicorn
from fastapi import FastAPI
from logger import configure_logging

from example_service.config import ServiceSettings, load_greeting_config
from example_service.exceptions import register_exception_handlers
from example_service.middleware import RequestContextMiddleware
from example_service.routers.greeting import router

configure_logging()

settings = ServiceSettings()

app = FastAPI(title="example-service")
app.state.greeting_config = load_greeting_config(settings.greeting_style)
app.add_middleware(RequestContextMiddleware)
register_exception_handlers(app)
app.include_router(router)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=settings.host)
    parser.add_argument("--port", type=int, default=settings.port)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
