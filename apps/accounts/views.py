from datetime import timedelta

from django.conf import settings
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserPreference
from apps.accounts.serializers import (
    AuthResponseSerializer,
    LoginSerializer,
    PreferenceSerializer,
    RegisterSerializer,
    UserSerializer,
)
from apps.workspaces.models import WorkspaceMembership
from apps.workspaces.serializers import WorkspaceSummarySerializer


def auth_payload(user, workspace=None):
    refresh = RefreshToken.for_user(user)
    payload = {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "token_type": "Bearer",
        "expires_in": int(
            settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()
        ),
        "user": UserSerializer(user).data,
    }
    if workspace is not None:
        payload["workspace"] = WorkspaceSummarySerializer(workspace).data
    return payload


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["authentication"],
        summary="Register a user and create their first workspace",
        request=RegisterSerializer,
        responses={201: AuthResponseSerializer},
        auth=[],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        workspace = (
            WorkspaceMembership.objects.filter(user=user)
            .select_related("workspace")
            .first()
            .workspace
        )
        return Response(
            auth_payload(user, workspace),
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_authenticate_header(self, request):
        # DRF downgrades AuthenticationFailed to 403 when there is no
        # authenticator to advertise. Login failures are authentication errors,
        # so advertise Bearer and keep the standard 401 response.
        return "Bearer"

    @extend_schema(
        tags=["authentication"],
        summary="Obtain JWT access and refresh tokens",
        request=LoginSerializer,
        responses={200: AuthResponseSerializer},
        auth=[],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        membership = (
            WorkspaceMembership.objects.filter(user=user)
            .select_related("workspace")
            .order_by("id")
            .first()
        )
        return Response(auth_payload(user, membership.workspace if membership else None))


class MeView(APIView):
    @extend_schema(
        tags=["authentication"],
        summary="Retrieve the authenticated user, preferences and workspaces",
        responses={200: UserSerializer},
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class PreferencesView(APIView):
    @extend_schema(
        tags=["authentication"],
        summary="Retrieve the authenticated user's personalization preferences",
        responses={200: PreferenceSerializer},
    )
    def get(self, request):
        preference, _ = UserPreference.objects.get_or_create(user=request.user)
        return Response(PreferenceSerializer(preference).data)

    @extend_schema(
        tags=["authentication"],
        summary="Update personalization preferences",
        request=PreferenceSerializer,
        responses={200: PreferenceSerializer},
    )
    def patch(self, request):
        with transaction.atomic():
            preference, _ = UserPreference.objects.get_or_create(user=request.user)
            serializer = PreferenceSerializer(
                preference, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(serializer.data)
