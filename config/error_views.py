"""JSON fallbacks for errors raised outside DRF's exception handling."""
import logging

from django.http import JsonResponse

logger = logging.getLogger(__name__)


def api_404(request, exception=None):
    return JsonResponse(
        {
            "error": {
                "code": "not_found",
                "message": "The requested resource was not found.",
            }
        },
        status=404,
    )


def api_500(request):
    # Never expose exception details, stack traces, or settings to clients.
    return JsonResponse(
        {
            "error": {
                "code": "server_error",
                "message": "An unexpected server error occurred.",
            }
        },
        status=500,
    )
