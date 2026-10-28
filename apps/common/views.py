import logging

from django.conf import settings
from django.db import DatabaseError, connection
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(
        tags=["system"],
        summary="API health check",
        description="Reports API and database availability without exposing secrets.",
        responses={200: OpenApiResponse(description="Service is healthy.")},
    )
    def get(self, request):
        database = "ok"
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except DatabaseError:
            logger.exception("Health check database failure")
            database = "unavailable"

        healthy = database == "ok"
        return Response(
            {
                "status": "ok" if healthy else "degraded",
                "api_version": "v1",
                "database": database,
                "ai_configured": bool(settings.GEMINI_API_KEY),
                "data_source": "simulated",
                "time": timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
