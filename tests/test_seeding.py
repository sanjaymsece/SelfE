from datetime import date, timedelta
from io import StringIO
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.models import User
from apps.analytics.models import PostInsight
from apps.comment_intelligence.models import Comment
from apps.social_accounts.models import Post, SocialAccount
from apps.workspaces.models import Workspace
from simulation.fixtures.demo_data import DEMO_USERS
from tests.support import APIBaseTest


class SeedDemoDataTests(APIBaseTest):
    reference = date(2026, 6, 30)

    def seed(self, reference=None):
        return call_command(
            "seed_demo_data",
            reference_date=(reference or self.reference).isoformat(),
            stdout=StringIO(),
        )

    def test_seed_creates_two_complete_simulated_tenants(self):
        self.seed()
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Workspace.objects.count(), 2)
        self.assertEqual(SocialAccount.objects.count(), 4)
        self.assertEqual(Post.objects.count(), 32)
        self.assertEqual(Comment.objects.count(), 28)
        self.assertTrue(PostInsight.objects.exists())

        for dataset in DEMO_USERS:
            user = User.objects.get(email=dataset["email"])
            self.assertTrue(user.check_password(settings.DEMO_PASSWORD))
            membership = user.workspace_memberships.select_related("workspace").get()
            self.assertEqual(membership.role, "owner")
            self.assertEqual(membership.workspace.slug, dataset["workspace_slug"])
            self.assertEqual(membership.workspace.timezone, dataset["timezone"])

        self.assertTrue(
            SocialAccount.objects.filter(is_simulated=True).count() == 4
        )
        self.assertTrue(Post.objects.filter(is_simulated=True).count() == 32)
        self.assertTrue(Comment.objects.filter(is_simulated=True).count() == 28)
        self.assertFalse(
            Comment.objects.exclude(sentiment="unknown").exists()
        )
        self.assertFalse(Comment.objects.exclude(analyzed_at__isnull=True).exists())

    def test_seed_is_idempotent_for_the_same_reference_date(self):
        self.seed()
        insight_rows = list(
            PostInsight.objects.order_by("id").values_list(
                "id", "post_id", "date", "views", "reach", "likes"
            )
        )
        comment_rows = list(
            Comment.objects.order_by("id").values_list(
                "id", "external_id", "text", "commented_at"
            )
        )
        post_rows = list(
            Post.objects.order_by("id").values_list(
                "id", "external_id", "published_at"
            )
        )

        self.seed()

        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Workspace.objects.count(), 2)
        self.assertEqual(SocialAccount.objects.count(), 4)
        self.assertEqual(Post.objects.count(), 32)
        self.assertEqual(Comment.objects.count(), 28)
        self.assertEqual(
            list(
                PostInsight.objects.order_by("id").values_list(
                    "id", "post_id", "date", "views", "reach", "likes"
                )
            ),
            insight_rows,
        )
        self.assertEqual(
            list(
                Comment.objects.order_by("id").values_list(
                    "id", "external_id", "text", "commented_at"
                )
            ),
            comment_rows,
        )
        self.assertEqual(
            list(
                Post.objects.order_by("id").values_list(
                    "id", "external_id", "published_at"
                )
            ),
            post_rows,
        )

    def test_reseeding_with_a_new_reference_date_replaces_stale_insight_windows(self):
        self.seed(date(2026, 6, 30))
        new_reference = date(2026, 10, 22)
        self.seed(new_reference)

        self.assertEqual(Post.objects.count(), 32)
        self.assertEqual(Comment.objects.count(), 28)
        self.assertTrue(PostInsight.objects.exists())

        for post in Post.objects.select_related("workspace"):
            tz = ZoneInfo(post.workspace.timezone)
            local_date = post.published_at.astimezone(tz).date()
            expected_count = min(10, (new_reference - local_date).days + 1)
            dates = list(
                post.insights.order_by("date").values_list("date", flat=True)
            )
            self.assertEqual(len(dates), expected_count)
            self.assertEqual(dates[0], local_date)
            self.assertEqual(dates[-1], local_date + timedelta(days=expected_count - 1))
            self.assertLessEqual(dates[-1], new_reference)

    def test_invalid_reference_date_raises_command_error(self):
        with self.assertRaises(CommandError):
            call_command(
                "seed_demo_data",
                reference_date="not-a-date",
                stdout=StringIO(),
            )
