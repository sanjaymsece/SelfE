from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.throttling import AIUserThrottle
from apps.reel_generator.models import ReelPlan
from apps.reel_generator.selectors import reels_for_workspace
from apps.reel_generator.serializers import (
    ReelGenerateSerializer,
    ReelPlanCreateSerializer,
    ReelPlanQuerySerializer,
    ReelPlanSerializer,
)
from apps.reel_generator.services import generate_reel_plan
from apps.workspaces.mixins import WORKSPACE_HEADER_PARAMETER, WorkspaceMixin


@extend_schema(
    tags=["reel generator"],
    summary="Generate a structured Reel production plan",
    description=(
        "Uses saved preferences and the authenticated workspace's simulated "
        "performance context. The validated plan covers hooks, scenes, dialogue, "
        "camera angles, lighting, backgrounds, music, captions, and a CTA. The "
        "plan is saved as a draft and nothing is saved if AI generation fails."
    ),
    parameters=[WORKSPACE_HEADER_PARAMETER],
    request=ReelGenerateSerializer,
    responses={201: ReelPlanSerializer},
)
class GenerateReelView(WorkspaceMixin, APIView):
    throttle_classes = [AIUserThrottle]

    def post(self, request):
        serializer = ReelGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = generate_reel_plan(
            workspace=self.get_workspace(),
            user=request.user,
            request_data=serializer.validated_data,
        )
        return Response(ReelPlanSerializer(plan).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["reel generator"],
    summary="List saved Reel plans or create a validated manual plan",
    description=(
        "POST accepts a complete plan that matches the same ReelPlanResult "
        "schema used for AI generation. The workspace and creator are always "
        "taken from the authenticated request."
    ),
    parameters=[WORKSPACE_HEADER_PARAMETER],
    request=ReelPlanCreateSerializer,
    responses={200: ReelPlanSerializer(many=True), 201: ReelPlanSerializer},
)
class ReelPlanListCreateView(WorkspaceMixin, ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReelPlanCreateSerializer
        return ReelPlanSerializer

    def get_queryset(self):
        data = ReelPlanQuerySerializer(data=self.request.query_params)
        data.is_valid(raise_exception=True)
        return reels_for_workspace(
            self.get_workspace(),
            status=data.validated_data.get("status"),
            platform=data.validated_data.get("platform"),
            search=data.validated_data.get("search"),
        )

    def perform_create(self, serializer):
        serializer.save(
            workspace=self.get_workspace(),
            created_by=self.request.user,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            ReelPlanSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["reel generator"],
    summary="Retrieve, update, or delete a saved Reel plan",
    parameters=[WORKSPACE_HEADER_PARAMETER],
    request=ReelPlanSerializer,
    responses={200: ReelPlanSerializer, 204: None},
)
class ReelPlanDetailView(WorkspaceMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = ReelPlanSerializer

    def get_queryset(self):
        return ReelPlan.objects.filter(workspace=self.get_workspace())
