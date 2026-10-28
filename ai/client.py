"""Shared Gemini provider client.

All feature services call the provider through ai.service, which uses
`get_ai_client`. Tests replace that callable with ai.mock.MockAIClient.
"""

from dataclasses import dataclass
import json
import logging
import time
from typing import Any

import httpx
from django.conf import settings
from django.utils.module_loading import import_string
from pydantic import BaseModel, ValidationError

from ai.exceptions import (
    AINotConfigured,
    AIProviderError,
    AIQuotaExceeded,
    AITimeout,
    AIInvalidResponse,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AIResult:
    data: dict[str, Any]
    model: str
    prompt_tokens: int | None = None
    output_tokens: int | None = None


class BaseAIClient:
    provider = "base"
    model = ""

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema: type[BaseModel],
        temperature: float | None = None,
    ) -> AIResult:
        raise NotImplementedError


class GeminiAIClient(BaseAIClient):
    provider = "gemini"

    def __init__(self, api_key: str | None = None):
        key = (api_key or settings.GEMINI_API_KEY).strip()
        if not key:
            raise AINotConfigured("GEMINI_API_KEY is empty.")
        self.model = settings.GEMINI_MODEL.strip()
        if not self.model:
            raise AINotConfigured("GEMINI_MODEL is empty.")

        try:
            from google import genai
            from google.genai import errors, types
        except Exception as exc:  # pragma: no cover - import failure is environmental
            raise AINotConfigured("google-genai is not available.") from exc

        self._errors = errors
        self._types = types
        timeout_ms = max(1000, int(settings.GEMINI_TIMEOUT_SECONDS * 1000))
        try:
            self._client = genai.Client(
                api_key=key,
                http_options=types.HttpOptions(timeout=timeout_ms),
            )
        except Exception as exc:
            raise AINotConfigured("Gemini client could not be initialised.") from exc

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema: type[BaseModel],
        temperature: float | None = None,
    ) -> AIResult:
        if not prompt or len(prompt) > settings.GEMINI_MAX_PROMPT_CHARS:
            raise AIProviderError("Prompt was empty or exceeded the configured limit.")

        attempts = max(1, settings.GEMINI_MAX_ATTEMPTS)
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=self._types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=(
                            settings.GEMINI_TEMPERATURE
                            if temperature is None
                            else temperature
                        ),
                        max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
                    ),
                )
                data = self._extract(response, response_schema)
                usage = getattr(response, "usage_metadata", None)
                return AIResult(
                    data=data,
                    model=str(getattr(response, "model_version", "") or self.model),
                    prompt_tokens=self._usage_value(usage, "prompt_token_count"),
                    output_tokens=self._usage_value(usage, "candidates_token_count"),
                )
            except (AIInvalidResponse, AINotConfigured, AIQuotaExceeded) as exc:
                raise exc
            except (httpx.TimeoutException, TimeoutError) as exc:
                last_error = AITimeout("Gemini request timed out.")
            except self._errors.APIError as exc:
                code = int(getattr(exc, "code", 0) or 0)
                logger.warning(
                    "gemini_api_error code=%s attempt=%s/%s",
                    code,
                    attempt,
                    attempts,
                )
                if code in (401, 403, 404):
                    raise AINotConfigured(
                        "Gemini credentials or the configured model are not usable."
                    ) from exc
                if code == 429:
                    last_error = AIQuotaExceeded("Gemini quota or rate limit reached.")
                elif code >= 500:
                    last_error = AIProviderError("Gemini server error.")
                else:
                    raise AIProviderError("Gemini rejected the request.") from exc
            except (ValidationError, json.JSONDecodeError, ValueError) as exc:
                raise AIInvalidResponse("Gemini response did not match the schema.") from exc
            except httpx.TransportError as exc:
                last_error = AIProviderError("Gemini network transport error.")
            except Exception as exc:
                logger.warning("gemini_unexpected_error class=%s", exc.__class__.__name__)
                raise AIProviderError("Unexpected Gemini client error.") from exc

            if attempt < attempts:
                # Bounded exponential backoff for transient provider failures.
                time.sleep(min(0.5 * (2 ** (attempt - 1)), 4.0))

        raise last_error or AIProviderError("Gemini request failed.")

    @staticmethod
    def _usage_value(usage, name: str) -> int | None:
        if usage is None:
            return None
        value = getattr(usage, name, None)
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract(response, response_schema: type[BaseModel]) -> dict[str, Any]:
        parsed = getattr(response, "parsed", None)
        if parsed is not None:
            if isinstance(parsed, BaseModel):
                return parsed.model_dump()
            if isinstance(parsed, dict):
                return response_schema.model_validate(parsed).model_dump()
            return response_schema.model_validate(parsed).model_dump()

        text = getattr(response, "text", None)
        if not text:
            raise AIInvalidResponse("Gemini returned no text.")
        return response_schema.model_validate_json(text).model_dump()


def get_ai_client() -> BaseAIClient:
    """Instantiate the configured provider. No fallback provider is attempted."""
    try:
        client_class = import_string(settings.AI_CLIENT_CLASS)
    except Exception as exc:
        raise AINotConfigured("Configured AI client class could not be imported.") from exc
    return client_class()
