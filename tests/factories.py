from dataclasses import dataclass
from datetime import date, datetime, time, timezone as dt_timezone
import uuid

from django.utils.text import slugify
from rest_framework.test import APIClient

from apps.accounts.models import User, UserPreference
from apps.analytics.models import AnalyticsReport, PostInsight
from apps.comment_intelligence.models import Comment
from apps.content_studio.models import ContentDraft, DraftKind, DraftSource
from apps.reel_generator.models import ReelPlan
from apps.social_accounts.models import Post, SocialAccount
from apps.workspaces.models import MembershipRole, Workspace, WorkspaceMembership

TEST_PASSWORD = "TestPass123!"


@dataclass
class Tenant:
    user: User
    workspace: Workspace
    preference: UserPreference


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def create_tenant(
    *,
    email: str | None = None,
    password: str = TEST_PASSWORD,
    workspace_name: str | None = None,
    slug: str | None = None,
    niche: str = "plant-based cooking",
    timezone_name: str = "UTC",
    goals: list[str] | None = None,
    tone: str = "friendly",
    content_style: str = "educational",
    target_audience: str = "home cooks",
    preferred_language: str = "en",
) -> Tenant:
    suffix = _uid()
    email = email or f"user-{suffix}@example.com"
    workspace_name = workspace_name or f"Test Workspace {suffix}"
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=f"User {suffix}",
    )
    workspace = Workspace.objects.create(
        name=workspace_name,
        slug=slug or f"{slugify(workspace_name)[:120]}-{suffix}",
        niche=niche,
        timezone=timezone_name,
        created_by=user,
    )
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role=MembershipRole.OWNER,
    )
    preference = UserPreference.objects.create(
        user=user,
        niche=niche,
        goals=goals or ["grow the audience"],
        tone=tone,
        content_style=content_style,
        target_audience=target_audience,
        preferred_language=preferred_language,
        keywords=["test"],
    )
    return Tenant(user=user, workspace=workspace, preference=preference)


def add_workspace_membership(user: User, workspace_name: str) -> Workspace:
    suffix = _uid()
    workspace = Workspace.objects.create(
        name=workspace_name,
        slug=f"{slugify(workspace_name)}-{suffix}",
        niche="secondary niche",
        timezone="UTC",
        created_by=user,
    )
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role=MembershipRole.MEMBER,
    )
    return workspace


def api_client_for(tenant: Tenant, *, workspace_id: int | None = None) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=tenant.user)
    client.credentials(HTTP_X_WORKSPACE_ID=str(workspace_id or tenant.workspace.id))
    return client


def create_social_account(
    workspace: Workspace,
    *,
    platform: str = "instagram",
    handle: str | None = None,
    follower_count: int = 10000,
) -> SocialAccount:
    return SocialAccount.objects.create(
        workspace=workspace,
        platform=platform,
        handle=handle or f"@test_{_uid()}",
        display_name="Test account",
        follower_count=follower_count,
        is_simulated=True,
    )


def aware_datetime(
    year: int, month: int, day: int, hour: int = 9, minute: int = 0
) -> datetime:
    return datetime(
        year, month, day, hour, minute, tzinfo=dt_timezone.utc
    )


def create_post(
    workspace: Workspace,
    *,
    social_account: SocialAccount | None = None,
    external_id: str | None = None,
    caption: str = "Test post caption",
    media_type: str = "reel",
    published_at: datetime | None = None,
) -> Post:
    account = social_account or create_social_account(workspace)
    return Post.objects.create(
        workspace=workspace,
        social_account=account,
        external_id=external_id or f"post-{_uid()}",
        caption=caption,
        media_type=media_type,
        permalink="https://simulated.example/post",
        published_at=published_at or aware_datetime(2026, 3, 1, 9),
        is_simulated=True,
    )


def create_insight(
    post: Post,
    *,
    day: date,
    views: int = 1000,
    reach: int = 500,
    likes: int = 50,
    comments: int = 5,
    shares: int = 5,
    saves: int = 5,
) -> PostInsight:
    if reach > views:
        raise ValueError("reach cannot exceed views")
    return PostInsight.objects.create(
        workspace=post.workspace,
        post=post,
        date=day,
        views=views,
        reach=reach,
        likes=likes,
        comments=comments,
        shares=shares,
        saves=saves,
    )


def create_comment(
    post: Post,
    *,
    external_id: str | None = None,
    author_username: str = "commenter",
    text: str = "Interesting post!",
    commented_at: datetime | None = None,
    like_count: int = 0,
) -> Comment:
    return Comment.objects.create(
        workspace=post.workspace,
        post=post,
        external_id=external_id or f"comment-{_uid()}",
        author_username=author_username,
        text=text,
        commented_at=commented_at or aware_datetime(2026, 3, 2, 10),
        like_count=like_count,
        is_simulated=True,
    )


def create_draft(
    workspace: Workspace,
    *,
    user: User | None = None,
    kind: str = DraftKind.CAPTION,
    title: str = "Saved draft",
) -> ContentDraft:
    return ContentDraft.objects.create(
        workspace=workspace,
        created_by=user,
        kind=kind,
        title=title,
        body="Draft body",
        content={"text": "Draft content"},
        source=DraftSource.MANUAL,
    )


def create_reel_plan(
    workspace: Workspace,
    *,
    user: User | None = None,
    title: str = "Saved reel",
) -> ReelPlan:
    return ReelPlan.objects.create(
        workspace=workspace,
        created_by=user,
        title=title,
        topic="Test topic",
        platform="instagram",
        target_duration_seconds=30,
        plan={"title": title, "scenes": []},
    )


def create_report(
    workspace: Workspace,
    *,
    user: User | None = None,
    date_from: date = date(2026, 2, 1),
    date_to: date = date(2026, 2, 7),
    findings: list[str] | None = None,
) -> AnalyticsReport:
    return AnalyticsReport.objects.create(
        workspace=workspace,
        created_by=user,
        date_from=date_from,
        date_to=date_to,
        metrics={"totals": {"views": 100}},
        explanation={
            "summary": "A saved test report.",
            "growth_explanation": "No baseline.",
            "key_findings": findings or ["A saved finding."],
            "recommendations": ["Keep posting."],
        },
        model_used="mock-gemini",
    )
