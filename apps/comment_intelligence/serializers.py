from rest_framework import serializers

from apps.comment_intelligence.models import (
    Comment,
    CommentIntent,
    CommentReplySuggestion,
    CommentSentiment,
)


class CommentSerializer(serializers.ModelSerializer):
    post = serializers.IntegerField(source="post_id", read_only=True)
    post_caption = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "post",
            "post_caption",
            "author_username",
            "text",
            "commented_at",
            "like_count",
            "sentiment",
            "intent",
            "is_question",
            "is_collaboration_opportunity",
            "confidence",
            "analysis_summary",
            "analyzed_at",
            "is_simulated",
            "created_at",
        ]

    def get_post_caption(self, obj) -> str:
        return (obj.post.caption or "")[:300]


class CommentQuerySerializer(serializers.Serializer):
    sentiment = serializers.ChoiceField(choices=CommentSentiment.choices, required=False)
    intent = serializers.ChoiceField(choices=CommentIntent.choices, required=False)
    post = serializers.IntegerField(min_value=1, required=False)
    is_question = serializers.BooleanField(required=False, allow_null=True)
    analyzed = serializers.BooleanField(required=False, allow_null=True)
    search = serializers.CharField(max_length=200, required=False, allow_blank=True)


class CommentAnalysisRequestSerializer(serializers.Serializer):
    comment_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=False,
        max_length=50,
    )

    def validate_comment_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("comment_ids must be unique.")
        return value


class ReplyRequestSerializer(serializers.Serializer):
    tone = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=""
    )
    language = serializers.CharField(
        max_length=30, required=False, allow_blank=True, default=""
    )
    extra_instructions = serializers.CharField(
        max_length=500, required=False, allow_blank=True, default=""
    )


class CommentReplySuggestionSerializer(serializers.ModelSerializer):
    comment = serializers.IntegerField(source="comment_id", read_only=True)
    model_used = serializers.CharField(read_only=True)

    class Meta:
        model = CommentReplySuggestion
        fields = [
            "id",
            "comment",
            "suggestions",
            "tone",
            "model_used",
            "created_at",
        ]


class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            "sentiment",
            "intent",
            "is_question",
            "is_collaboration_opportunity",
            "analysis_summary",
        ]
