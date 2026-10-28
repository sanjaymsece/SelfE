from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from apps.common.models import TimeStampedModel
from apps.social_accounts.models import Post
from apps.workspaces.models import Workspace


class PostInsight(TimeStampedModel):
    """Daily, non-cumulative performance snapshot for one post.

    A row contains that day's totals. Query ranges sum rows. Metrics are
    simulated; no Meta/Instagram API is called.
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="post_insights",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="insights",
    )
    date = models.DateField(db_index=True)
    views = models.PositiveBigIntegerField(default=0)
    reach = models.PositiveBigIntegerField(default=0)
    likes = models.PositiveBigIntegerField(default=0)
    comments = models.PositiveBigIntegerField(default=0)
    shares = models.PositiveBigIntegerField(default=0)
    saves = models.PositiveBigIntegerField(default=0)

    class Meta:
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["post", "date"], name="post_insight_unique_post_date"
            ),
            models.CheckConstraint(
                condition=Q(reach__lte=F("views")),
                name="post_insight_reach_lte_views",
            ),
        ]
        indexes = [
            models.Index(fields=["workspace", "date"]),
            models.Index(fields=["post", "date"]),
        ]

    def __str__(self):
        return f"{self.post_id}@{self.date}"

    def save(self, *args, **kwargs):
        if self.post_id and self.post.workspace_id != self.workspace_id:
            raise ValidationError("Insight and post must belong to the same workspace.")
        if self.reach > self.views:
            raise ValidationError("Reach cannot exceed views.")
        super().save(*args, **kwargs)


class AnalyticsReport(TimeStampedModel):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="analytics_reports",
    )
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="analytics_reports",
    )
    date_from = models.DateField()
    date_to = models.DateField()
    metrics = models.JSONField(default=dict)
    explanation = models.JSONField(default=dict)
    model_used = models.CharField(max_length=100, blank=True)
    data_source = models.CharField(max_length=20, default="simulated")

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(date_from__lte=F("date_to")),
                name="analytics_report_valid_date_range",
            ),
        ]
        indexes = [models.Index(fields=["workspace", "-created_at"])]

    def __str__(self):
        return f"Report {self.pk} ({self.date_from} to {self.date_to})"
