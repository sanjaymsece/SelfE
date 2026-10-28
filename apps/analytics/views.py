from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.models import AnalyticsReport
from apps.analytics.selectors import (
    build_overview,
    post_metrics_for_range,
    posting_time_recommendations,
)
from apps.analytics.serializers import (
    AnalyticsPostQuerySerializer,
    AnalyticsReportSerializer,
    DateRangeQuerySerializer,
    PostingTimeQuerySerializer,
    ReportGenerateSerializer,
)
from apps.analytics.services import generate_analytics_report
from apps.common.throttling import AIUserThrottle
from apps.social_accounts.models import MediaType, SocialPlatform
from apps.workspaces.mixins import WORKSPACE_HEADER_PARAMETER, WorkspaceMixin


def _validated_query(serializer_class, query_params):
    serializer = serializer_class(data=query_params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


@extend_schema(
    tags=["analytics"],
    summary="Calculated analytics overview with historical comparison",
    description=(
        "All metrics are calculated in Python/Django from simulated daily "
        "post insights. The previous period is the immediately preceding range "
        "of equal length. No LLM is used for calculations."
    ),
    parameters=[WORKSPACE_HEADER_PARAMETER],
    responses={200: OpenApiResponse(description="Calculated analytics overview.")},
)
class AnalyticsOverviewView(WorkspaceMixin, APIView):
    def get(self, request):
        data = _validated_query(DateRangeQuerySerializer, request.query_params)
        return Response(build_overview(self.get_workspace(), data["date_range"]))


@extend_schema(
    tags=["analytics"],
    summary="Per-post analytics for a date range",
    parameters=[
        WORKSPACE_HEADER_PARAMETER,
        OpenApiParameter(name="date_from", type=str, required=False),
        OpenApiParameter(name="date_to", type=str, required=False),
        OpenApiParameter(
            name="platform",
            type=str,
            enum=SocialPlatform.values,
            required=False,
        ),
        OpenApiParameter(
            name="media_type",
            type=str,
            enum=MediaType.values,
            required=False,
        ),
    ],
    responses={200: OpenApiResponse(description="Paginated per-post metrics.")},
)
class AnalyticsPostsView(WorkspaceMixin, APIView):
    def get(self, request):
        data = _validated_query(AnalyticsPostQuerySerializer, request.query_params)
        rows = post_metrics_for_range(
            self.get_workspace(),
            data["date_range"],
            platform=data.get("platform"),
            media_type=data.get("media_type"),
        )
        paginator = self._paginator()
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response(page)

    @staticmethod
    def _paginator():
        from apps.common.pagination import StandardResultsSetPagination

        return StandardResultsSetPagination()


@extend_schema(
    tags=["analytics"],
    summary="List saved AI analytics reports",
    parameters=[WORKSPACE_HEADER_PARAMETER],
    responses={200: AnalyticsReportSerializer(many=True)},
)
class AnalyticsReportListView(WorkspaceMixin, ListAPIView):
    serializer_class = AnalyticsReportSerializer

    def get_queryset(self):
        return AnalyticsReport.objects.filter(
            workspace=self.get_workspace()
        ).order_by("-created_at", "-id")


@extend_schema(
    tags=["analytics"],
    summary="Retrieve one saved AI analytics report",
    parameters=[WORKSPACE_HEADER_PARAMETER],
    responses={200: AnalyticsReportSerializer},
)
class AnalyticsReportDetailView(WorkspaceMixin, RetrieveAPIView):
    serializer_class = AnalyticsReportSerializer

    def get_queryset(self):
        return AnalyticsReport.objects.filter(workspace=self.get_workspace())


@extend_schema(
    tags=["analytics"],
    summary="Generate an AI explanation of calculated analytics",
    description=(
        "Calculates metrics from the workspace's simulated post insights, asks "
        "Gemini to explain only those results, validates the response schema, and "
        "saves the report. If the AI provider fails, no report is saved and a "
        "structured error is returned."
    ),
    parameters=[WORKSPACE_HEADER_PARAMETER],
    request=ReportGenerateSerializer,
    responses={201: AnalyticsReportSerializer},
)
class GenerateAnalyticsReportView(WorkspaceMixin, APIView):
    throttle_classes = [AIUserThrottle]

    def post(self, request):
        serializer = ReportGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = generate_analytics_report(
            workspace=self.get_workspace(),
            user=request.user,
            date_range=serializer.validated_data["date_range"],
        )
        return Response(
            AnalyticsReportSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["analytics"],
    summary="Simulated historical posting-time recommendations",
    description=(
        "Groups each post once by its publication weekday/hour in the workspace "
        "timezone and ranks slots by mean per-post engagement rate. Recommendations "
        "are deterministic and based only on simulated historical records."
    ),
    parameters=[
        WORKSPACE_HEADER_PARAMETER,
        OpenApiParameter(name="date_from", type=str, required=False),
        OpenApiParameter(name="date_to", type=str, required=False),
        OpenApiParameter(
            name="platform",
            type=str,
            enum=SocialPlatform.values,
            required=False,
        ),
        OpenApiParameter(name="min_posts", type=int, required=False),
        OpenApiParameter(name="limit", type=int, required=False),
    ],
    responses={200: OpenApiResponse(description="Posting-time recommendations.")},
)
class PostingTimesView(WorkspaceMixin, APIView):
    def get(self, request):
        data = _validated_query(PostingTimeQuerySerializer, request.query_params)
        result = posting_time_recommendations(
            self.get_workspace(),
            data["date_range"],
            platform=data.get("platform"),
            min_sample=data.get("min_posts"),
            limit=data.get("limit"),
        )
        return Response(result)
