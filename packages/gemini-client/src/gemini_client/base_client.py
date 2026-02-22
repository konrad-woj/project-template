import asyncio
import base64
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any

from PIL.Image import MIME, Image

DEFAULT_SYSTEM_PROMPT = (
    "You are skilled in reading, creating and understanding technical documentation and "
    "drawings. You are helpful, precise and concise. Do not add any additional trivia, just "
    "answer the question."
)


class BaseLLMClient(ABC):
    """Base class for all Large Language Models."""

    input_token_cost: float = 0.0
    output_token_cost: float = 0.0

    def __init__(self, system_prompt: str = DEFAULT_SYSTEM_PROMPT, max_concurrent_calls: int = 10, **kwargs):
        self._default_system_prompt = system_prompt
        self._semaphore = asyncio.Semaphore(max_concurrent_calls)

    @abstractmethod
    def query(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        images: list[Image] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def query_async(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        images: list[Image] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        pass

    @staticmethod
    def encode_img(img: Image) -> tuple[str, str]:
        """Encode PIL Image to base64 string."""
        buffered = BytesIO()
        img.save(buffered, format=img.format)
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf8")
        mimetype = MIME.get(img.format or "") or ""
        return img_base64, mimetype
