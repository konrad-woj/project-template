"""Google Gemini LLM client with cost tracking, retry logic, and conversation history support.

This module provides a high-level interface to Google's Gemini models with automatic cost calculation, token usage,
retry logic with exponential backoff.

Usage Examples
--------------

1. Simple Prompt (Basic Usage)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from gemini_client.gemini import Gemini25Flash

    # Initialize client
    client = Gemini25Flash()

    # Send a simple prompt
    response = client.query("What is the capital of France?")

    print(response["text"])           # "The capital of France is Paris."
    print(response["input_tokens"])   # 7
    print(response["output_tokens"])  # 8
    print(response["cost"])           # 0.000023 (calculated automatically)


2. Conversation History (Chat Mode)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from gemini_client.gemini import Gemini25Flash

    client = Gemini25Flash()

    # Build conversation history
    history = [
        {"role": "user", "parts": ["Hi, I'm learning Python"]},
        {"role": "model", "parts": ["Hello! That's great! Python is a wonderful language. How can I help?"]},
        {"role": "user", "parts": ["Can you explain list comprehensions?"]},
        {"role": "model", "parts": ["Sure! List comprehensions are a concise way to create lists..."]},
    ]

    # Continue the conversation
    response = client.query(user_prompt="Can you show me an example?", history=history)

    print(response["text"])  # Model responds with context of previous conversation


3. Thinking Mode (Extended Reasoning)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from gemini_client.gemini import Gemini25Flash  # Must use thinking-capable model

    client = Gemini25Flash()

    # Enable thinking mode with token budget
    response = client.query(
        user_prompt="Solve this complex math problem: If a train leaves Chicago at 3pm...",
        thinking_config={"thinking_budget": 2000}  # Allow up to 2000 tokens for reasoning
    )

    print(response["text"])             # Final answer
    print(response["thinking_tokens"])  # Tokens used for internal reasoning
    print(response["thinking_cost"])    # Cost of thinking tokens


4. Async Usage with Images
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from gemini_client.gemini import Gemini25Flash
    from PIL import Image

    async def analyze_image():
        client = Gemini25Flash()

        # Load image
        img = Image.open("diagram.png")

        # Query with image
        response = await client.query_async(
            user_prompt="What does this diagram show?",
            images=[img]
        )

        return response["text"]


5. Custom Configuration
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from gemini_client.gemini import Gemini25Flash

    client = Gemini25Flash(
        system_prompt="You are a helpful Python coding assistant.",
        disable_safety_filters=False,  # Enable safety filters for production
        num_retries=3,
        request_timeout=120,
        request_params={"temperature": 0.7}  # Model parameters
    )

    response = client.query("Write a function to sort a list")


Environment Variables
---------------------
- GEMINI_API_KEY: Required - Your Google AI API key
- LANGFUSE_PUBLIC_KEY: Optional - For observability tracking
"""

import asyncio
import json
import os
import time
from collections.abc import Collection
from copy import copy
from typing import Any

import google.genai.errors
import httpx
import structlog
from google import genai
from google.genai import types
from logger.async_timer import async_timer
from PIL.Image import Image

from gemini_client.base_client import DEFAULT_SYSTEM_PROMPT, BaseLLMClient

logger = structlog.get_logger(__name__)

MAX_THINKING_BUDGET = 10000  # Reasonable upper limit for thinking tokens

# Langfuse decorator removed - not using observability


def _calculate_sleep_time(try_number: int) -> int:
    """Returns sleep time for exponential backoff.

    Sequence: 5s, 10s, 20s, 40s, 60s (capped).
    Designed to handle Gemini rate limits which often request ~30s waits.
    """
    return min(5 * (2**try_number), 60)


def _usage_metadata_to_json(usage_metadata: Any) -> dict[str, Any]:
    """Converts SDK UsageMetadata to JSON-serializable dict."""

    def default(obj):
        """Default JSON serializer that tries to call to_dict() or uses __dict__, else str()."""
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "__dict__"):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        elif isinstance(obj, list | tuple):
            return [default(item) for item in obj]
        return str(obj)

    if usage_metadata is None:
        return {}

    try:
        return json.loads(json.dumps(usage_metadata, default=default, ensure_ascii=False))
    except Exception:
        logger.warning("Failed to convert usage_metadata to JSON", usage_metadata=str(usage_metadata))
        return {}


def _extract_url_context_metadata(response: types.GenerateContentResponse) -> dict[str, Any]:
    """Extracts and normalizes url context metadata from a GenerateContentResponse.

    Returns a dict with keys: urls (list), num_successful, num_total. Returns {} on unexpected shape.
    """
    try:
        if response is None or response.candidates is None:
            return {}
        if len(response.candidates) != 1:
            logger.warning(
                "Unexpected number of candidates when extracting url_context_metadata",
                candidates=len(response.candidates),
            )
            # continue - try to extract from first candidate if present
        candidate = response.candidates[0]
        url_context = getattr(candidate, "url_context_metadata", None)
        if url_context is None or not getattr(url_context, "url_metadata", None):
            return {"urls": [], "num_successful": 0, "num_total": 0}

        metadata = {"urls": [], "num_successful": 0, "num_total": 0}
        for url_meta in url_context.url_metadata:
            status = getattr(url_meta, "url_retrieval_status", None)
            is_success = status == types.UrlRetrievalStatus.URL_RETRIEVAL_STATUS_SUCCESS
            if is_success:
                metadata["num_successful"] += 1
            metadata["urls"].append(
                {
                    "url": getattr(url_meta, "retrieved_url", None),
                    "success": is_success,
                    "status": status.name if status is not None else None,
                }
            )
        metadata["num_total"] = len(metadata["urls"])
        return metadata
    except Exception as e:
        logger.warning("Failed to extract URL context metadata", error=str(e))
        return {"num_successful": 0, "num_total": 0, "error": str(e)}


def _compute_costs_from_usage(usage_json: dict[str, Any], model: "GeminiLLM") -> dict[str, Any]:
    """Compute cost breakdown using token counts from usage_json and per-token rates from model."""
    prompt_tokens = usage_json.get("prompt_token_count", 0) or 0
    candidates_tokens = usage_json.get("candidates_token_count", 0) or 0
    thinking_tokens = usage_json.get("thoughts_token_count", 0) or 0
    tool_use_prompt_tokens = usage_json.get("tool_use_prompt_token_count", 0) or 0
    tool_use_output_tokens = usage_json.get("tool_use_output_token_count", 0) or 0
    url_prompt_tokens = usage_json.get("url_context_prompt_token_count", 0) or 0
    url_output_tokens = usage_json.get("url_context_output_token_count", 0) or 0

    # Fallback: try to classify any other url-related token counts if explicit keys are not present.
    for k, v in usage_json.items():
        if not isinstance(v, int | float):
            continue
        kl = k.lower()
        if "url" in kl and "token" in kl:
            # Skip already captured explicit keys.
            if kl in ("url_context_prompt_token_count", "url_context_output_token_count"):
                continue
            # Classify by presence of prompt/input or output/candidate/thought.
            if "prompt" in kl or "input" in kl or "tool" in kl:
                url_prompt_tokens += int(v)
            elif "output" in kl or "candidate" in kl or "thought" in kl:
                url_output_tokens += int(v)
            else:
                # Ambiguous -> treat as input (conservative).
                url_prompt_tokens += int(v)

    # Aggregate tokens.
    tool_use_tokens = tool_use_prompt_tokens + tool_use_output_tokens
    url_total_tokens = url_prompt_tokens + url_output_tokens
    total_input_tokens = prompt_tokens + tool_use_prompt_tokens + url_prompt_tokens
    total_output_tokens = candidates_tokens + thinking_tokens + tool_use_output_tokens + url_output_tokens

    # Compute costs.
    input_rate = getattr(model, "input_token_cost", None)
    output_rate = getattr(model, "output_token_cost", None)
    prompt_cost = (prompt_tokens * input_rate) if input_rate is not None else None
    tools_prompt_cost = (tool_use_prompt_tokens * input_rate) if input_rate is not None else None
    url_prompt_cost = (url_prompt_tokens * input_rate) if input_rate is not None else None
    tools_output_cost = (tool_use_output_tokens * output_rate) if output_rate is not None else None
    candidates_cost = (candidates_tokens * output_rate) if output_rate is not None else None
    thinking_cost = (thinking_tokens * output_rate) if output_rate is not None else None
    url_output_cost = (url_output_tokens * output_rate) if output_rate is not None else None

    # Aggregate costs.
    total_input_cost, total_output_cost, total_cost = None, None, None
    if any(x is not None for x in (prompt_cost, tools_prompt_cost, url_prompt_cost)):
        total_input_cost = sum(x or 0 for x in (prompt_cost, tools_prompt_cost, url_prompt_cost))
    if any(x is not None for x in (candidates_cost, thinking_cost, tools_output_cost, url_output_cost)):
        total_output_cost = sum(x or 0 for x in (candidates_cost, thinking_cost, tools_output_cost, url_output_cost))
    if total_input_cost is not None or total_output_cost is not None:
        total_cost = (total_input_cost or 0) + (total_output_cost or 0)

    return {
        "cost": total_cost,
        # Detailed costs:
        "input_cost": total_input_cost,
        "output_cost": total_output_cost,
        "thinking_cost": thinking_cost,
        "tools_prompt_cost": tools_prompt_cost,
        "tools_output_cost": tools_output_cost,
        "url_prompt_cost": url_prompt_cost,
        "url_output_cost": url_output_cost,
        "prompt_cost": prompt_cost,
        "candidates_cost": candidates_cost,
        # Aggregate token counts:
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        # Detailed token counts:
        "thinking_tokens": thinking_tokens,
        "prompt_tokens": prompt_tokens,
        "candidates_tokens": candidates_tokens,
        "tool_use_prompt_tokens": tool_use_prompt_tokens,
        "tool_use_output_tokens": tool_use_output_tokens,
        "tool_use_tokens": tool_use_tokens,
        "url_prompt_tokens": url_prompt_tokens,
        "url_output_tokens": url_output_tokens,
        "url_tokens": url_total_tokens,
    }


class GeminiLLM(BaseLLMClient):
    """Base class for all Gemini Large Language Models."""

    model_id: str | None = None
    # whether the model can think, if so, budget will be set to 0 by default
    has_thinking: bool = False

    def __init__(
        self,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_concurrent_calls: int = 10,
        request_params: dict | None = None,
        num_retries: int = 5,
        request_timeout: int = 180,
        disable_safety_filters: bool = True,
        no_retry_codes: Collection[int] = (400, 401, 403, 404),
    ):
        """Initialize GeminiLLM instance.

        Args:
            system_prompt: The system prompt to use for the request.
            max_concurrent_calls: Maximum number of concurrent async calls.
            request_params: params to pass to the request body (e.g. temperature etc).
            num_retries: Number of times to retry the request before giving up in case of API or HTTP error.
            request_timeout: Timeout in seconds to wait for the request to complete.
            disable_safety_filters: If True, disable all safety filters (BLOCK_NONE). Use with caution in production.
                                   If False, use Gemini's default safety settings.
            no_retry_codes: List of HTTP error codes to not retry on.
        """
        super().__init__(system_prompt=system_prompt, max_concurrent_calls=max_concurrent_calls)

        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if gemini_api_key is None:
            raise ValueError("GEMINI_API_KEY not set")
        self.client = genai.Client(api_key=gemini_api_key)
        self.request_params = request_params or {}
        self.num_retries = num_retries
        self.request_timeout = request_timeout
        self.disable_safety_filters = disable_safety_filters
        self.no_retry_codes = no_retry_codes
        # Track whether we've closed the async client to avoid double-closing and races.
        self._aio_closed = False
        # Lock to serialize asynchronous close operations and avoid race conditions.
        self._aio_close_lock = asyncio.Lock()

        if self.model_id is None:
            raise ValueError("This is base class and should not be instantiated. Please instantiate child classes.")

    def _process_response(self, response: Any, start_time: float) -> dict[str, Any]:
        """Process the API response and calculate costs, include usage and url context metadata."""

        usage_json = _usage_metadata_to_json(response.usage_metadata) if response is not None else {}
        cost_metadata = _compute_costs_from_usage(usage_json, self)

        input_tokens = cost_metadata.get("input_tokens", 0)
        output_tokens = cost_metadata.get("output_tokens", 0)
        thought_tokens = cost_metadata.get("thinking_tokens", 0)
        total_tokens = int(input_tokens + output_tokens)
        usage_json["total_token_count"] = total_tokens

        # Handle finish reason (e.g. if MAX_TOKENS is reached)
        if response is not None and response.candidates is not None and len(response.candidates) == 1:
            candidate = response.candidates[0]
            finish_reason = candidate.finish_reason.value if candidate.finish_reason is not None else None
            if finish_reason != "STOP":
                logger.warning("Generation did not complete correctly", finish_reason=finish_reason)
        else:
            logger.warning(
                "Unexpected number of candidates. Currently only single-candidate responses are supported.",
                candidates=len(response.candidates)
                if response is not None and response.candidates is not None
                else None,
            )
            finish_reason = None

        url_context_metadata = _extract_url_context_metadata(response)

        return {
            "response": response.text if response is not None else None,
            "text": response.text if response is not None else None,
            "raw_response": response,
            "usage_metadata_obj": getattr(response, "usage_metadata", None),
            "model": response.model_version if response is not None else None,
            "model_version": response.model_version if response is not None else None,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "thought_tokens": thought_tokens,
            "answer_time": time.time() - start_time,
            "input_cost": cost_metadata.get("input_cost"),
            "output_cost": cost_metadata.get("output_cost"),
            "finish_reason": finish_reason,
            "parsed": getattr(response, "parsed", None) if response is not None else None,
            # Normalized/extra metadata for consumers:
            "usage_metadata": usage_json,
            "cost_metadata": cost_metadata,
            "url_context_metadata": url_context_metadata,
            "total_tokens": total_tokens,
            "total_token_count": total_tokens,
        }

    def send_request(self, contents: list[Any], config: types.GenerateContentConfig) -> types.GenerateContentResponse:
        try:
            if not self.model_id:
                raise ValueError("model_id is not set")
            return self.client.models.generate_content(
                model=self.model_id,
                contents=contents,
                config=config,
            )
        except httpx.HTTPError as e:
            logger.error("Got HTTPError", error_class=e.__class__.__name__, error=str(e))
            raise
        except google.genai.errors.APIError as e:
            logger.error(
                "Got Google API Error",
                error_class=e.__class__.__name__,
                code=e.code,
                status=e.status,
                message=str(e),
                error_details=getattr(e, "details", None),
            )
            raise

    async def send_request_async(
        self, contents: list[Any], config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        if self._aio_closed:
            raise RuntimeError("Cannot send request: client is closed")

        try:
            if not self.model_id:
                raise ValueError("model_id is not set")
            async with self._semaphore:
                try:
                    # the request seemed to hang sometimes so a timeout should make it retry if that happens
                    response = await asyncio.wait_for(
                        self.client.aio.models.generate_content(
                            model=self.model_id,
                            contents=contents,
                            config=config,
                        ),
                        timeout=self.request_timeout,
                    )
                    return response
                except asyncio.exceptions.TimeoutError:
                    logger.error("Async request timed out", timeout=self.request_timeout)
                    raise
        except httpx.HTTPError as e:
            logger.error("Got HTTPError", error_class=e.__class__.__name__, error=str(e))
            raise
        except google.genai.errors.APIError as e:
            logger.error(
                "Got Google API Error",
                error_class=e.__class__.__name__,
                code=e.code,
                status=e.status,
                message=str(e),
                error_details=getattr(e, "details", None),
            )
            raise

    def send_request_with_retry(
        self, contents: list[Any], config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        for retry in range(self.num_retries):
            try:
                return self.send_request(contents=contents, config=config)
            except google.genai.errors.ClientError as e:
                # Don't retry permanent 4xx client errors
                if e.code in self.no_retry_codes:
                    logger.error("Client error, not retrying", code=e.code, error=str(e))
                    raise
                # Retry 5xx server errors
                if retry == self.num_retries - 1:
                    raise
                sleep_time = _calculate_sleep_time(retry)
                logger.info("Retrying request", sleep_time=sleep_time, retry=retry + 1)
                time.sleep(sleep_time)
            except (httpx.HTTPError, asyncio.exceptions.TimeoutError):
                if retry == self.num_retries - 1:
                    raise
                sleep_time = _calculate_sleep_time(retry)
                logger.info("Retrying request", sleep_time=sleep_time, retry=retry + 1)
                time.sleep(sleep_time)

        raise RuntimeError("Exhausted all retries")

    async def send_request_async_with_retry(
        self, contents: list[Any], config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        for retry in range(self.num_retries):
            try:
                return await self.send_request_async(contents=contents, config=config)
            except google.genai.errors.ClientError as e:
                # Don't retry permanent 4xx client errors
                if e.code in self.no_retry_codes:
                    logger.error("Client error, not retrying", code=e.code, error=str(e))
                    raise
                # Retry 5xx server errors
                if retry == self.num_retries - 1:
                    raise
                sleep_time = _calculate_sleep_time(retry)
                logger.warning("Retrying async request", sleep_time=sleep_time, retry=retry + 1)
                await asyncio.sleep(sleep_time)
            except (httpx.HTTPError, asyncio.exceptions.TimeoutError, google.genai.errors.ServerError):
                if retry == self.num_retries - 1:
                    raise
                sleep_time = _calculate_sleep_time(retry)
                logger.warning("Retrying async request", sleep_time=sleep_time, retry=retry + 1)
                await asyncio.sleep(sleep_time)

        raise RuntimeError("Exhausted all retries")

    def prepare_request(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        images: list[Image] | None = None,
        history: list[dict[str, Any]] | None = None,
        **kwargs: Any | None,
    ) -> tuple[types.GenerateContentConfig, list[Any]]:
        """Prepare request configuration and contents.

        Args:
            user_prompt: The user's message
            system_prompt: Optional system prompt override
            images: Optional list of PIL Images
            history: Optional conversation history as list of dicts with 'role' and 'parts' keys
            **kwargs: Additional parameters (e.g., temperature, thinking_config)

        Returns:
            Tuple of (config, contents) - ready for API call
        """
        config = copy(self.request_params)
        config.update(kwargs)

        # Build contents (with or without history)
        contents = self._build_contents(user_prompt, images, history)

        # Handle thinking config
        thinking_config = self._build_thinking_config(config)

        # Build config dict
        config_params = {
            "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True),
            "system_instruction": system_prompt or self._default_system_prompt,
            **config,
        }

        # Add optional configs
        if self.disable_safety_filters:
            config_params["safety_settings"] = self._get_disabled_safety_settings()
        if thinking_config is not None:
            config_params["thinking_config"] = thinking_config

        return types.GenerateContentConfig(**config_params), contents

    def _build_contents(
        self, user_prompt: str, images: list[Image] | None, history: list[dict[str, Any]] | None
    ) -> list[Any]:
        """Build contents list from prompt, images, and optional history."""
        current_parts = [*images, user_prompt] if images else [user_prompt]

        if history is None:
            # No history - use simple format (backward compatible)
            return current_parts

        # Convert history to SDK Content objects
        def to_parts(parts_raw: list[Any]) -> list[Any]:
            """Convert parts to SDK format (strings become Part objects)."""
            return [types.Part(text=p) if isinstance(p, str) else p for p in parts_raw]

        contents = [
            types.Content(role=turn.get("role", "user"), parts=to_parts(turn.get("parts", []))) for turn in history
        ]
        contents.append(types.Content(role="user", parts=to_parts(current_parts)))
        return contents

    def _build_thinking_config(self, config: dict[str, Any]) -> types.ThinkingConfig | None:
        """Build and validate thinking config if provided."""
        if "thinking_config" not in config:
            return None

        if not self.has_thinking:
            raise ValueError(f"Model {self.model_id} does not support thinking_config")

        thinking_dict = config.pop("thinking_config")

        # Basic validation (let SDK handle detailed validation)
        if "thinking_budget" in thinking_dict:
            budget = thinking_dict["thinking_budget"]
            if not isinstance(budget, int) or budget < 0:
                raise ValueError(f"thinking_budget must be a non-negative integer, got {budget}")
            if budget > MAX_THINKING_BUDGET:
                logger.warning("Large thinking_budget", budget=budget, max_budget=MAX_THINKING_BUDGET)

        return types.ThinkingConfig(**thinking_dict)

    def _get_disabled_safety_settings(self) -> list[types.SafetySetting]:
        """Get safety settings that disable all filters."""
        return [
            types.SafetySetting(category=cat, threshold=types.HarmBlockThreshold.BLOCK_NONE)
            for cat in [
                types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            ]
        ]

    def query(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        images: list[Image] | None = None,
        history: list[dict[str, Any]] | None = None,
        **kwargs: Any | None,
    ) -> dict[str, Any]:
        start_time = time.time()
        config, contents = self.prepare_request(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            images=images,
            history=history,
            **kwargs,
        )
        response = self.send_request_with_retry(contents=contents, config=config)
        return self._process_response(response, start_time)

    @async_timer(level="DEBUG")
    async def query_async(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        images: list[Image] | None = None,
        history: list[dict[str, Any]] | None = None,
        **kwargs: Any | None,
    ) -> dict[str, Any]:
        start_time = time.time()
        config, contents = self.prepare_request(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            images=images,
            history=history,
            **kwargs,
        )

        response = await self.send_request_async_with_retry(contents=contents, config=config)
        return self._process_response(response, start_time)

    async def aclose(self) -> None:
        """Asynchronously close any underlying aio resources held by the GenAI client.

        Call this when you want to explicitly release network resources.
        """
        if self._aio_closed:
            return

        async with self._aio_close_lock:
            # Re-check after acquiring the lock to avoid race conditions
            if self._aio_closed:
                return
            try:
                if hasattr(self, "client") and hasattr(self.client, "aio"):
                    aio_client = self.client.aio
                    if hasattr(aio_client, "aclose"):
                        logger.debug("Closing Gemini aio client")
                        await aio_client.aclose()
            except Exception as e:
                logger.warning("Error closing Gemini aio client", error=str(e))
            finally:
                self._aio_closed = True

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures connections are closed."""
        await self.aclose()
        return None

    def close(self) -> None:
        """Synchronously close any underlying resources if supported.

        Note: prefer `await client.aclose()` in async code to close async resources.
        This method only closes synchronous resources and does NOT close async connections.
        """
        try:
            client = getattr(self, "client", None)
            if client is not None:
                close_fn = getattr(client, "close", None)
                if callable(close_fn):
                    close_fn()
        except Exception as e:
            logger.debug("Error while closing Gemini client synchronously", error=str(e))


### Stable models ###


class Gemini2Flash(GeminiLLM):
    """Stable"""

    model_id = "gemini-2.0-flash-001"
    input_token_cost = 1e-7
    output_token_cost = 4e-7


class Gemini2FlashLite(GeminiLLM):
    """Stable"""

    model_id = "gemini-2.0-flash-lite"
    input_token_cost = 7.5e-8
    output_token_cost = 3e-7


class Gemini25Flash(GeminiLLM):
    """Stable"""

    model_id = "gemini-2.5-flash"
    input_token_cost = 3e-7
    output_token_cost = 2.5e-6
    has_thinking = True


class Gemini25FlashLite(GeminiLLM):
    """Stable"""

    model_id = "gemini-2.5-flash-lite"
    input_token_cost = 1e-7
    output_token_cost = 4e-7
    has_thinking = True


class Gemini25Pro(GeminiLLM):
    """Stable"""

    model_id = "gemini-2.5-pro"
    input_token_cost = 1.25e-6
    output_token_cost = 1e-5
    has_thinking = True


### Experimental ###


class GeminiFlashLatest(GeminiLLM):
    """Experimental, results and costs may change"""

    model_id = "gemini-flash-latest"
    input_token_cost = 3e-7
    output_token_cost = 2.5e-6
    has_thinking = True


class GeminiFlashLiteLatest(GeminiLLM):
    """Experimental, results and costs may change"""

    model_id = "gemini-flash-lite-latest"
    input_token_cost = 1e-7
    output_token_cost = 4e-7
    has_thinking = True
