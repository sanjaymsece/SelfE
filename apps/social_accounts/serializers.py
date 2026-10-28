from rest_framework import serializers

from apps.social_accounts.models import SocialAccount, SocialPlatform


class SocialAccountSerializer(serializers.ModelSerializer):
    platform_display = serializers.CharField(
        source="get_platform_display", read_only=True
    )
    posts_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = SocialAccount
        fields = [
            "id",
            "platform",
            "platform_display",
            "handle",
            "display_name",
            "follower_count",
            "posts_count",
            "is_simulated",
            "created_at",
        ]


class SocialAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialAccount
        fields = ["platform", "handle", "display_name", "follower_count"]

    def validate_handle(self, value):
        cleaned = value.strip().lstrip("@")
        if not cleaned:
            raise serializers.ValidationError("Handle cannot be empty.")
        return cleaned
