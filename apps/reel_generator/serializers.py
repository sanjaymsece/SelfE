from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from ai.schemas import ReelPlanResult
from apps.reel_generator.models import ReelPlan, ReelStatus
from apps.social_accounts.models import SocialPlatform


class ReelGenerateSerializer(serializers.Serializer):
    topic = serializers.CharField(min_length=2, max_length=200)
    platform = serializers.ChoiceField(
        choices=SocialPlatform.choices, default=SocialPlatform.INSTAGRAM
    )
    duration_seconds = serializers.IntegerField(min_value=15, max_value=90, default=30)
    style = serializers.CharField(
        max_length=80, required=False, allow_blank=True, default=""
    )
    audience = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default=""
    )
    extra_instructions = serializers.CharField(
        max_length=1000, required=False, allow_blank=True, default=""
    )


class ReelPlanSerializer(serializers.ModelSerializer):
    plan = serializers.JSONField(read_only=True)
    model_used = serializers.CharField(read_only=True)

    class Meta:
        model = ReelPlan
        fields = [
            "id",
            "title",
            "topic",
            "platform",
            "target_duration_seconds",
            "status",
            "notes",
            "plan",
            "model_used",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "topic",
            "platform",
            "target_duration_seconds",
            "plan",
            "model_used",
            "created_at",
            "updated_at",
        ]

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be blank.")
        return value


class ReelPlanCreateSerializer(serializers.ModelSerializer):
    """Create a manually supplied plan using the same schema as AI output."""

    plan = serializers.JSONField()

    class Meta:
        model = ReelPlan
        fields = [
            "id",
            "title",
            "topic",
            "platform",
            "target_duration_seconds",
            "status",
            "notes",
            "plan",
        ]
        read_only_fields = ["id"]

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def validate_plan(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Plan must be a JSON object.")
        try:
            return ReelPlanResult.model_validate(value).model_dump()
        except PydanticValidationError as exc:
            details = [
                {
                    "field": ".".join(str(part) for part in error["loc"]),
                    "message": error["msg"],
                }
                for error in exc.errors()
            ]
            raise serializers.ValidationError(
                {"message": "Plan does not match the ReelPlanResult schema.", "errors": details}
            ) from exc


class ReelPlanQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ReelStatus.choices, required=False)
    platform = serializers.ChoiceField(choices=SocialPlatform.choices, required=False)
    search = serializers.CharField(max_length=200, required=False, allow_blank=True)
