"""Feature-facing AI orchestration with validation and usage tracking."""

from __future__ import annotations

import logging
import time
from typing import Callable

from django.conf import settings
from pydantic import BaseModel, ValidationError

from ai.client import get_ai_client
from ai.exceptions import AIError, AIInvalidResponse, AIProviderError
from ai.schemas import (
    AnalyticsExplanation,
    CaptionsResult,
    CommentAnalysisResult,
    ContentIdeasResult,
    ReplySuggestionsResult,
    ReelPlanResult,
    ScriptsResult,
)
from apps.common.models import AIUsageLog

logger = logging.getLogger("ai")

_SCHEMA_TO_FEATURE_DEFAULT = {
    AnalyticsExplanation: "analytics_report",
    ContentIdeasResult: "content_ideas",
    CaptionsResult: "content_captions",
    ScriptsResult: "content_scripts",
    ReelPlanResult: "reel_plan",
    CommentAnalysisResult: "comment_analysis",
    ReplySuggestionsResult: "comment_reply",
}


def _record_usage(
    *,
    workspace,
    user,
    feature: str,
    model: str,
    success: bool,
    latency_ms: int,
    error_kind: str = "",
    prompt_tokens: int | None = None,
    output_tokens: int | None = None,
) -> None:
    """Usage metadata only: never prompts, outputs, tokens, or API keys."""
    try:
        AIUsageLog.objects.create(
            workspace=workspace,
            user=user,
            feature=feature,
            provider="gemini",
            model=model[:100],
            success=success,
            error_kind=error_kind[:60],
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
        )
    except Exception:
        # Usage telemetry must not break the feature, and must not log secrets.
        logger.exception("Failed to record AI usage metadata")


def generate_ai_structured(
    *,
    feature: str,
    workspace,
    user,
    prompt: str,
    response_schema: type[BaseModel],
    temperature: float | None = None,
    validator: Callable[[BaseModel], None] | None = None,
) -> BaseModel:
    """Call the provider, validate output, and record safe usage metadata.

    Raises an AIError subclass on any failure. `validator` performs feature-level
    checks (for example, that every requested comment ID was classified) inside
    the same error/usage-tracking boundary.

    Callers must not save or return generated content unless this function
    returns successfully.
    """
    if not prompt or len(prompt) > settings.GEMINI_MAX_PROMPT_CHARS:
        raise AIProviderError("Prompt exceeded the configured safety limit.")

    started = time.monotonic()
    client = None
    result = None
    model = settings.GEMINI_MODEL or "unknown"

    try:
        client = get_ai_client()
        result = client.generate_structured(
            prompt=prompt,
            response_schema=response_schema,
            temperature=temperature,
        )
        parsed = response_schema.model_validate(result.data)
        if validator is not None:
            validator(parsed)
    except AIError as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        _record_usage(
            workspace=workspace,
            user=user,
            feature=feature,
            model=model,
            success=False,
            error_kind=exc.kind,
            latency_ms=latency_ms,
        )
        logger.warning(
            "ai_feature_failed feature=%s kind=%s schema=%s",
            feature,
            exc.kind,
            response_schema.__name__,
        )
        raise
    except (ValidationError, TypeError, ValueError) as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        _record_usage(
            workspace=workspace,
            user=user,
            feature=feature,
            model=(getattr(result, "model", None) or model),
            success=False,
            error_kind=AIInvalidResponse.kind,
            latency_ms=latency_ms,
        )
        logger.warning(
            "ai_feature_invalid_output feature=%s schema=%s",
            feature,
            response_schema.__name__,
        )
        raise AIInvalidResponse("AI output failed schema validation.") from exc
    except Exception as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        _record_usage(
            workspace=workspace,
            user=user,
            feature=feature,
            model=model,
            success=False,
            error_kind=AIProviderError.kind,
            latency_ms=latency_ms,
        )
        logger.warning(
            "ai_feature_unexpected feature=%s class=%s",
            feature,
            exc.__class__.__name__,
        )
        raise AIProviderError("Unexpected AI client failure.") from exc

    latency_ms = int((time.monotonic() - started) * 1000)
    used_model = result.model or model
    _record_usage(
        workspace=workspace,
        user=user,
        feature=feature,
        model=used_model,
        success=True,
        latency_ms=latency_ms,
        prompt_tokens=result.prompt_tokens,
        output_tokens=result.output_tokens,
    )
    return parsed
