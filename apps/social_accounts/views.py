from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.social_accounts.models import SocialAccount, SocialPlatform
from apps.social_accounts.selectors import social_accounts_for_workspace
from apps.social_accounts.serializers import (
    SocialAccountCreateSerializer,
    SocialAccountSerializer,
)
from apps.workspaces.mixins import WORKSPACE_HEADER_PARAMETER, WorkspaceMixin


@extend_schema(
    tags=["social accounts"],
    summary="List or connect simulated social accounts in the active workspace",
    parameters=[
        WORKSPACE_HEADER_PARAMETER,
        OpenApiParameter(
            name="platform",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            enum=SocialPlatform.values,
        ),
    ],
    responses={200: SocialAccountSerializer(many=True), 201: SocialAccountSerializer},
)
class SocialAccountListView(WorkspaceMixin, ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "POST":
            return SocialAccountCreateSerializer
        return SocialAccountSerializer

    def get_queryset(self):
        platform = self.request.query_params.get("platform")
        if platform and platform not in SocialPlatform.values:
            raise ValidationError({"platform": ["Unsupported platform."]})
        return social_accounts_for_workspace(self.get_workspace(), platform=platform)

    def create(self, request, *args, **kwargs):
        workspace = self.get_workspace()
        serializer = SocialAccountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save(workspace=workspace, is_simulated=True)
        return Response(
            SocialAccountSerializer(account).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["social accounts"],
    summary="Retrieve or disconnect a simulated social account",
    parameters=[WORKSPACE_HEADER_PARAMETER],
    responses={200: SocialAccountSerializer, 204: None},
)
class SocialAccountDetailView(WorkspaceMixin, RetrieveDestroyAPIView):
    serializer_class = SocialAccountSerializer

    def get_queryset(self):
        return social_accounts_for_workspace(self.get_workspace())


@extend_schema(
    tags=["social accounts"],
    summary="Connect live Instagram account using Meta Graph API token",
    parameters=[WORKSPACE_HEADER_PARAMETER],
    request=inline_serializer(
        name="InstagramLiveConnectRequest",
        fields={
            "access_token": serializers.CharField(required=True),
            "handle": serializers.CharField(required=False, default="sophia.studio"),
        },
    ),
    responses={200: inline_serializer(
        name="InstagramLiveConnectResponse",
        fields={
            "status": serializers.CharField(),
            "message": serializers.CharField(),
        },
    )},
)
class InstagramLiveConnectView(WorkspaceMixin, APIView):
    """
    Connect live Instagram Creator/Business account using Meta User Access Token.
    """
    def post(self, request, *args, **kwargs):
        from apps.social_accounts.instagram_client import InstagramGraphAPIClient
        token = request.data.get("access_token", "")
        handle = request.data.get("handle", "sophia.studio")

        if not token:
            return Response({"error": "access_token is required"}, status=status.HTTP_400_BAD_REQUEST)

        client = InstagramGraphAPIClient(token)
        result = client.sync_to_workspace(self.get_workspace(), instagram_handle=handle)
        return Response(result, status=status.HTTP_200_OK)
