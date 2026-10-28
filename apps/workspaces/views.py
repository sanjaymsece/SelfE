from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.workspaces.models import MembershipRole, Workspace, WorkspaceMembership
from apps.workspaces.serializers import (
    WorkspaceCreateSerializer,
    WorkspaceDetailSerializer,
)


@extend_schema(
    tags=["workspaces"],
    summary="List all accessible workspaces or create a new workspace",
    responses={200: WorkspaceDetailSerializer(many=True), 201: WorkspaceDetailSerializer},
)
class WorkspaceListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WorkspaceCreateSerializer
        return WorkspaceDetailSerializer

    def get_queryset(self):
        return Workspace.objects.for_user(self.request.user).order_by("id")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        workspace = serializer.save()
        output_serializer = WorkspaceDetailSerializer(workspace, context={"request": request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["workspaces"],
    summary="Retrieve, update, or delete a workspace",
    responses={200: WorkspaceDetailSerializer},
)
class WorkspaceDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WorkspaceDetailSerializer

    def get_queryset(self):
        return Workspace.objects.for_user(self.request.user)

    def perform_update(self, serializer):
        workspace = self.get_object()
        membership = WorkspaceMembership.objects.filter(
            workspace=workspace, user=self.request.user
        ).first()
        if not membership or membership.role not in (MembershipRole.OWNER, MembershipRole.ADMIN):
            raise PermissionDenied("Only workspace owners and admins can update settings.")
        serializer.save()

    def perform_destroy(self, instance):
        membership = WorkspaceMembership.objects.filter(
            workspace=instance, user=self.request.user
        ).first()
        if not membership or membership.role != MembershipRole.OWNER:
            raise PermissionDenied("Only workspace owners can delete a workspace.")
        instance.delete()
