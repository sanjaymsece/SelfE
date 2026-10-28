from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils.text import slugify
from rest_framework import serializers

from apps.workspaces.models import (
    MembershipRole,
    Workspace,
    WorkspaceMembership,
)


class WorkspaceSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ["id", "name", "slug", "niche", "timezone"]


class MembershipSerializer(serializers.ModelSerializer):
    workspace = WorkspaceSummarySerializer(read_only=True)

    class Meta:
        model = WorkspaceMembership
        fields = ["role", "workspace"]


class WorkspaceCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    niche = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    timezone = serializers.CharField(max_length=64, required=False, default="UTC")

    def validate_timezone(self, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise serializers.ValidationError("Unknown IANA timezone.") from exc
        return value

    @staticmethod
    def _unique_slug(name: str) -> str:
        base = slugify(name)[:150] or "workspace"
        slug = base
        suffix = 2
        while Workspace.objects.filter(slug=slug).exists():
            slug = f"{base[:150 - len(str(suffix)) - 1]}-{suffix}"
            suffix += 1
        return slug

    def create(self, validated_data):
        user = self.context["request"].user
        name = validated_data["name"].strip()
        workspace = Workspace.objects.create(
            name=name,
            slug=self._unique_slug(name),
            niche=validated_data.get("niche", ""),
            timezone=validated_data.get("timezone", "UTC"),
            created_by=user,
        )
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=user,
            role=MembershipRole.OWNER,
        )
        return workspace


class WorkspaceDetailSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    social_accounts_count = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            "id",
            "name",
            "slug",
            "niche",
            "timezone",
            "role",
            "members_count",
            "social_accounts_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "role",
            "members_count",
            "social_accounts_count",
            "created_at",
            "updated_at",
        ]

    def get_role(self, obj) -> str:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            membership = obj.memberships.filter(user=request.user).first()
            return membership.role if membership else ""
        return ""

    def get_members_count(self, obj) -> int:
        return obj.memberships.count()

    def get_social_accounts_count(self, obj) -> int:
        return obj.social_accounts.count()
