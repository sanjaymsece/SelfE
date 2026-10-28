from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from apps.common.models import TimeStampedModel
from apps.social_accounts.models import Post
from apps.workspaces.models import Workspace


class CommentSentiment(models.TextChoices):
    UNKNOWN = "unknown", "Unknown"
    POSITIVE = "positive", "Positive"
    NEUTRAL = "neutral", "Neutral"
    NEGATIVE = "negative", "Negative"


class CommentIntent(models.TextChoices):
    UNKNOWN = "unknown", "Unknown"
    QUESTION = "question", "Question"
    COLLABORATION = "collaboration", "Collaboration"
    PRAISE = "praise", "Praise"
    COMPLAINT = "complaint", "Complaint"
    FEEDBACK = "feedback", "Feedback"
    SPAM = "spam", "Spam"
    OTHER = "other", "Other"


class Comment(TimeStampedModel):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    external_id = models.CharField(max_length=100)
    author_username = models.CharField(max_length=100)
    text = models.TextField()
    commented_at = models.DateTimeField()
    like_count = models.PositiveIntegerField(default=0)
    sentiment = models.CharField(
        max_length=20,
        choices=CommentSentiment.choices,
        default=CommentSentiment.UNKNOWN,
    )
    intent = models.CharField(
        max_length=20,
        choices=CommentIntent.choices,
        default=CommentIntent.UNKNOWN,
    )
    is_question = models.BooleanField(default=False)
    is_collaboration_opportunity = models.BooleanField(default=False)
    confidence = models.FloatField(null=True, blank=True)
    analysis_summary = models.TextField(blank=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)
    is_simulated = models.BooleanField(default=True)

    class Meta:
        ordering = ["-commented_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "external_id"],
                name="comment_unique_external_id_per_workspace",
            ),
            models.CheckConstraint(
                condition=Q(confidence__isnull=True)
                | (Q(confidence__gte=0) & Q(confidence__lte=1)),
                name="comment_confidence_between_zero_and_one",
            ),
        ]
        indexes = [
            models.Index(fields=["workspace", "-commented_at"]),
            models.Index(fields=["workspace", "sentiment"]),
            models.Index(fields=["workspace", "intent"]),
            models.Index(fields=["post", "-commented_at"]),
        ]

    def __str__(self):
        return f"@{self.author_username}: {self.text[:40]}"

    def save(self, *args, **kwargs):
        if self.post_id and self.post.workspace_id != self.workspace_id:
            raise ValidationError("Comment and post must belong to the same workspace.")
        super().save(*args, **kwargs)


class CommentReplySuggestion(TimeStampedModel):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="comment_reply_suggestions",
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="reply_suggestions",
    )
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="comment_reply_suggestions",
    )
    suggestions = models.JSONField(default=list)
    tone = models.CharField(max_length=50, blank=True)
    model_used = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["comment", "-created_at"]),
            models.Index(fields=["workspace", "-created_at"]),
        ]

    def __str__(self):
        return f"Reply suggestions for comment {self.comment_id}"

    def save(self, *args, **kwargs):
        if self.comment_id and self.comment.workspace_id != self.workspace_id:
            raise ValidationError(
                "Reply suggestions and comment must belong to the same workspace."
            )
        super().save(*args, **kwargs)
