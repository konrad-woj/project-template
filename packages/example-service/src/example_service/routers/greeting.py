from example_library import build_greeting
from fastapi import APIRouter, Request
from logger import get_logger

from example_service.config import GreetingConfig
from example_service.exceptions import NameTooLongError
from example_service.models import GreetingResponse

router = APIRouter(prefix="/greetings", tags=["greetings"])
log = get_logger(__name__)


def _build_message(name: str, config: GreetingConfig) -> str:
    if config.template is None:
        return build_greeting(name)
    return config.template.format(name=name)


@router.get("/{name}", response_model=GreetingResponse)
async def get_greeting(name: str, request: Request) -> GreetingResponse:
    config: GreetingConfig = request.app.state.greeting_config
    if len(name) > config.max_name_length:
        raise NameTooLongError(name=name, max_length=config.max_name_length)
    log.info("greeting.served", name=name)
    return GreetingResponse(message=_build_message(name, config))
