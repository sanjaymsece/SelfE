from datetime import date

from rest_framework import serializers

from apps.analytics.models import AnalyticsReport
from apps.analytics.selectors import DateRange, resolve_date_range
from apps.social_accounts.models import MediaType, SocialPlatform


class DateRangeQuerySerializer(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        attrs["date_range"] = resolve_date_range(
            attrs.get("date_from"), attrs.get("date_to")
        )
        return attrs


class AnalyticsPostQuerySerializer(DateRangeQuerySerializer):
    platform = serializers.ChoiceField(
        choices=SocialPlatform.choices, required=False
    )
    media_type = serializers.ChoiceField(choices=MediaType.choices, required=False)


class PostingTimeQuerySerializer(DateRangeQuerySerializer):
    platform = serializers.ChoiceField(
        choices=SocialPlatform.choices, required=False
    )
    min_posts = serializers.IntegerField(min_value=1, max_value=20, required=False)
    limit = serializers.IntegerField(min_value=1, max_value=20, required=False)


class ReportGenerateSerializer(DateRangeQuerySerializer):
    pass


class AnalyticsReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsReport
        fields = [
            "id",
            "date_from",
            "date_to",
            "metrics",
            "explanation",
            "model_used",
            "data_source",
            "created_at",
        ]
