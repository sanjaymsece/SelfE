from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from apps.common.models import TimeStampedModel


class WorkspaceQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(memberships__user=user).distinct()


class Workspace(TimeStampedModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    niche = models.CharField(max_length=120, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_workspaces",
    )

    objects = WorkspaceQuerySet.as_manager()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name

    def validate_timezone(self):
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValidationError({"timezone": "Unknown IANA timezone."}) from exc

    def save(self, *args, **kwargs):
        self.validate_timezone()
        if not self.slug:
            self.slug = slugify(self.name)[:150] or "workspace"
        super().save(*args, **kwargs)


class MembershipRole(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"


class WorkspaceMembership(TimeStampedModel):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=MembershipRole.choices,
        default=MembershipRole.MEMBER,
    )

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "user"],
                name="workspace_membership_unique_user",
            ),
        ]
        indexes = [models.Index(fields=["user", "workspace"])]

    def __str__(self):
        return f"{self.user_id} in {self.workspace_id} ({self.role})"
