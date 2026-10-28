from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimeStampedModel
from apps.workspaces.models import Workspace


class SocialPlatform(models.TextChoices):
    INSTAGRAM = "instagram", "Instagram"
    TIKTOK = "tiktok", "TikTok"
    YOUTUBE = "youtube", "YouTube"
    FACEBOOK = "facebook", "Facebook"
    LINKEDIN = "linkedin", "LinkedIn"


class MediaType(models.TextChoices):
    IMAGE = "image", "Image"
    CAROUSEL = "carousel", "Carousel"
    REEL = "reel", "Reel"
    VIDEO = "video", "Video"


class SocialAccount(TimeStampedModel):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )
    platform = models.CharField(max_length=30, choices=SocialPlatform.choices)
    handle = models.CharField(max_length=100)
    display_name = models.CharField(max_length=150, blank=True)
    follower_count = models.PositiveIntegerField(default=0)
    is_simulated = models.BooleanField(
        default=True,
        help_text="All records in this project are simulated; no Meta API is used.",
    )

    class Meta:
        ordering = ["platform", "handle"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "platform", "handle"],
                name="social_account_unique_handle_per_platform",
            ),
        ]
        indexes = [models.Index(fields=["workspace", "platform"])]

    def __str__(self):
        return f"{self.get_platform_display()} {self.handle}"


class Post(TimeStampedModel):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    social_account = models.ForeignKey(
        SocialAccount,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    external_id = models.CharField(max_length=100)
    caption = models.TextField(blank=True)
    media_type = models.CharField(
        max_length=20,
        choices=MediaType.choices,
        default=MediaType.IMAGE,
    )
    permalink = models.URLField(blank=True)
    published_at = models.DateTimeField()
    is_simulated = models.BooleanField(default=True)

    class Meta:
        ordering = ["-published_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["social_account", "external_id"],
                name="post_unique_external_id_per_account",
            ),
        ]
        indexes = [
            models.Index(fields=["workspace", "-published_at"]),
            models.Index(fields=["social_account", "-published_at"]),
        ]

    def __str__(self):
        return f"{self.social_account_id}:{self.external_id}"

    def save(self, *args, **kwargs):
        if self.social_account_id and self.social_account.workspace_id != self.workspace_id:
            raise ValidationError("Post and social account must belong to the same workspace.")
        super().save(*args, **kwargs)
