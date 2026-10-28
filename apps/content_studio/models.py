from django.db import models

from apps.common.models import TimeStampedModel
from apps.workspaces.models import Workspace


class DraftKind(models.TextChoices):
    IDEA = "idea", "Content idea"
    CAPTION = "caption", "Caption"
    SCRIPT = "script", "Script"


class DraftStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    APPROVED = "approved", "Approved"
    ARCHIVED = "archived", "Archived"


class DraftSource(models.TextChoices):
    MANUAL = "manual", "Manual"
    AI = "ai", "AI generated"


class ContentDraft(TimeStampedModel):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="content_drafts",
    )
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="content_drafts",
    )
    kind = models.CharField(max_length=20, choices=DraftKind.choices)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    content = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=DraftStatus.choices,
        default=DraftStatus.DRAFT,
    )
    source = models.CharField(
        max_length=20,
        choices=DraftSource.choices,
        default=DraftSource.MANUAL,
    )
    model_used = models.CharField(max_length=100, blank=True)
    prompt_context = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["workspace", "-created_at"]),
            models.Index(fields=["workspace", "kind", "status"]),
        ]

    def __str__(self):
        return f"{self.kind}: {self.title}"
