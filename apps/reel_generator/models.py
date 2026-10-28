from django.db import models

from apps.common.models import TimeStampedModel
from apps.social_accounts.models import SocialPlatform
from apps.workspaces.models import Workspace


class ReelStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    APPROVED = "approved", "Approved"
    ARCHIVED = "archived", "Archived"


class ReelPlan(TimeStampedModel):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="reel_plans",
    )
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reel_plans",
    )
    title = models.CharField(max_length=150)
    topic = models.CharField(max_length=200)
    platform = models.CharField(
        max_length=30,
        choices=SocialPlatform.choices,
        default=SocialPlatform.INSTAGRAM,
    )
    target_duration_seconds = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20, choices=ReelStatus.choices, default=ReelStatus.DRAFT
    )
    notes = models.TextField(blank=True)
    plan = models.JSONField(default=dict)
    model_used = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["workspace", "-created_at"]),
            models.Index(fields=["workspace", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(target_duration_seconds__gt=0),
                name="reel_plan_positive_target_duration",
            )
        ]

    def __str__(self):
        return self.title
