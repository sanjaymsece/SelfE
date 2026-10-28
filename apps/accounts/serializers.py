from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.models import User, UserPreference
from apps.workspaces.models import (
    MembershipRole,
    Workspace,
    WorkspaceMembership,
)
from apps.workspaces.serializers import MembershipSerializer


class PreferenceSerializer(serializers.ModelSerializer):
    goals = serializers.ListField(
        child=serializers.CharField(max_length=200),
        max_length=10,
        required=False,
    )
    keywords = serializers.ListField(
        child=serializers.CharField(max_length=50),
        max_length=20,
        required=False,
    )

    class Meta:
        model = UserPreference
        fields = [
            "niche",
            "goals",
            "preferred_language",
            "tone",
            "content_style",
            "target_audience",
            "keywords",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class UserSerializer(serializers.ModelSerializer):
    preferences = serializers.SerializerMethodField()
    workspaces = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "date_joined", "preferences", "workspaces"]

    @extend_schema_field(PreferenceSerializer)
    def get_preferences(self, obj):
        preference = getattr(obj, "preferences", None) or UserPreference(user=obj)
        return PreferenceSerializer(preference).data

    @extend_schema_field(MembershipSerializer(many=True))
    def get_workspaces(self, obj):
        memberships = obj.workspace_memberships.select_related("workspace").order_by("id")
        return MembershipSerializer(memberships, many=True).data


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        min_length=10,
        max_length=128,
        trim_whitespace=False,
    )
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    workspace_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True
    )
    niche = serializers.CharField(max_length=120, required=False, allow_blank=True)
    goals = serializers.ListField(
        child=serializers.CharField(max_length=200),
        max_length=10,
        required=False,
    )
    preferred_language = serializers.CharField(
        max_length=30, required=False, default="en"
    )
    tone = serializers.CharField(max_length=50, required=False, default="friendly")
    content_style = serializers.CharField(
        max_length=50, required=False, default="educational"
    )
    target_audience = serializers.CharField(
        max_length=200, required=False, allow_blank=True
    )
    workspace_timezone = serializers.CharField(
        max_length=64, required=False, default="UTC"
    )

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return normalized

    def validate_workspace_timezone(self, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise serializers.ValidationError("Unknown IANA timezone.") from exc
        return value

    def validate(self, attrs):
        candidate = User(email=attrs.get("email", ""), full_name=attrs.get("full_name", ""))
        validate_password(attrs["password"], user=candidate)
        return attrs

    @staticmethod
    def _unique_slug(name: str) -> str:
        base = slugify(name)[:150] or "workspace"
        slug = base
        suffix = 2
        while Workspace.objects.filter(slug=slug).exists():
            slug = f"{base[:150 - len(str(suffix)) - 1]}-{suffix}"
            suffix += 1
        return slug

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data.get("full_name", ""),
        )
        workspace_name = (
            validated_data.get("workspace_name", "").strip()
            or f"{user.display_name}'s Workspace"
        )
        workspace = Workspace.objects.create(
            name=workspace_name,
            slug=self._unique_slug(workspace_name),
            niche=validated_data.get("niche", ""),
            timezone=validated_data.get("workspace_timezone", "UTC"),
            created_by=user,
        )
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=user,
            role=MembershipRole.OWNER,
        )
        UserPreference.objects.create(
            user=user,
            niche=validated_data.get("niche", ""),
            goals=validated_data.get("goals", []),
            preferred_language=validated_data.get("preferred_language", "en"),
            tone=validated_data.get("tone", "friendly"),
            content_style=validated_data.get("content_style", "educational"),
            target_audience=validated_data.get("target_audience", ""),
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        max_length=128,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        request = self.context.get("request")
        user = authenticate(
            request=request,
            username=email,
            password=attrs["password"],
        )
        if user is None or not user.is_active:
            # Deliberately does not reveal whether the email exists.
            raise AuthenticationFailed("Invalid email or password.")
        attrs["user"] = user
        return attrs


class AuthResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    token_type = serializers.CharField()
    expires_in = serializers.IntegerField()
    user = UserSerializer()
    workspace = serializers.DictField(required=False, allow_null=True)
