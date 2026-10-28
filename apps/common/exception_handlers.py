import logging

from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from ai.exceptions import AIError

logger = logging.getLogger(__name__)


def _payload(code: str, message: str, details=None) -> dict:
    error = {"code": code, "message": message}
    if details not in (None, {}, []):
        error["details"] = details
    return {"error": error}


def _drf_error_response(exc, response):
    data = response.data
    message = None
    details = None
    code = getattr(exc, "default_code", None) or "error"

    if isinstance(exc, exceptions.ValidationError):
        code = "validation_error"
        message = "Request validation failed."
        details = data
    elif isinstance(data, dict) and set(data.keys()) == {"detail"}:
        message = str(data["detail"])
        code = getattr(exc, "default_code", None) or "error"
    elif isinstance(data, dict):
        details = data
        message = str(data.get("detail") or "The request could not be completed.")
    elif isinstance(data, list):
        details = {"non_field_errors": data}
        message = "The request could not be completed."
    else:
        message = str(data)

    if isinstance(exc, exceptions.Throttled):
        code = "throttled"
        wait = getattr(exc, "wait", None)
        message = "Request limit reached. Please try again later."
        if wait:
            details = {"retry_after_seconds": int(wait)}

    # Django's Http404 (and DRF's NotFound) are converted to a response before
    # this handler sees them, but Http404 itself has no DRF default_code.
    if response.status_code == status.HTTP_404_NOT_FOUND:
        code = "not_found"

    if message is None:
        message = "The request could not be completed."

    return Response(
        _payload(code, message, details),
        status=response.status_code,
        headers=response.headers,
    )


def api_exception_handler(exc, context):
    if isinstance(exc, AIError):
        # Provider/internal details are logged by the AI service; the client only
        # receives a safe code and message.
        return Response(
            _payload(exc.kind, exc.public_message),
            status=exc.http_status,
        )

    response = drf_exception_handler(exc, context)
    if response is not None:
        return _drf_error_response(exc, response)

    # Unhandled exceptions become a generic JSON 500. Never render a stack trace
    # or internal error text in the response.
    logger.exception("Unhandled API exception")
    return Response(
        _payload("server_error", "An unexpected server error occurred."),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
