from rest_framework import serializers

from apps.content_studio.models import ContentDraft, DraftKind, DraftStatus
from apps.social_accounts.models import SocialPlatform


class ContentDraftSerializer(serializers.ModelSerializer):
    source = serializers.CharField(read_only=True)
    model_used = serializers.CharField(read_only=True)

    class Meta:
        model = ContentDraft
        fields = [
            "id",
            "kind",
            "title",
            "body",
            "content",
            "status",
            "source",
            "model_used",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "source", "model_used", "created_at", "updated_at"]

    def validate_content(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Content must be a JSON object.")
        return value


class ContentGenerationBaseSerializer(serializers.Serializer):
    platform = serializers.ChoiceField(
        choices=SocialPlatform.choices, default=SocialPlatform.INSTAGRAM
    )
    topic = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default=""
    )
    goal = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default=""
    )
    tone = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=""
    )
    language = serializers.CharField(
        max_length=30, required=False, allow_blank=True, default=""
    )
    extra_instructions = serializers.CharField(
        max_length=1000, required=False, allow_blank=True, default=""
    )


class ContentIdeasRequestSerializer(ContentGenerationBaseSerializer):
    count = serializers.IntegerField(min_value=1, max_value=10, default=5)


class CaptionsRequestSerializer(ContentGenerationBaseSerializer):
    count = serializers.IntegerField(min_value=1, max_value=10, default=5)


class ScriptsRequestSerializer(ContentGenerationBaseSerializer):
    count = serializers.IntegerField(min_value=1, max_value=3, default=1)


class ContentDraftQuerySerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=DraftKind.choices, required=False)
    status = serializers.ChoiceField(choices=DraftStatus.choices, required=False)
    search = serializers.CharField(max_length=200, required=False, allow_blank=True)
