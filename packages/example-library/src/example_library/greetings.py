from logger import get_logger

log = get_logger(__name__)


def build_greeting(name: str) -> str:
    log.debug("greeting.built", name=name)
    return f"Hello, {name}!"
