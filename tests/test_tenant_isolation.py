from datetime import date, timedelta

from django.utils import timezone

from tests.factories import (
    api_client_for,
    aware_datetime,
    create_comment,
    create_draft,
    create_insight,
    create_post,
    create_reel_plan,
    create_report,
    create_social_account,
    create_tenant,
)
from tests.support import APIBaseTest, mocked_ai


class TenantIsolationTests(APIBaseTest):
    def setUp(self):
        self.tenant_a = create_tenant(
            email="a@example.com",
            workspace_name="Tenant A",
            niche="TENANT-A-NICHE",
        )
        self.tenant_b = create_tenant(
            email="b@example.com",
            workspace_name="Tenant B",
            niche="B-SECRET-NICHE",
        )

        self.account_a = create_social_account(
            self.tenant_a.workspace, handle="@tenant_a"
        )
        self.account_b = create_social_account(
            self.tenant_b.workspace, handle="@tenant_b"
        )
        self.post_a = create_post(
            self.tenant_a.workspace,
            social_account=self.account_a,
            caption="A-ONLY historical caption",
            published_at=aware_datetime(2026, 2, 1, 9),
        )
        self.post_b = create_post(
            self.tenant_b.workspace,
            social_account=self.account_b,
            caption="B-SECRET-TENANT historical caption",
            published_at=aware_datetime(2026, 2, 1, 9),
        )
        create_insight(self.post_a, day=date(2026, 2, 1), views=100, reach=50)
        create_insight(self.post_b, day=date(2026, 2, 1), views=999, reach=500)

        # Recent posts exercise the cross-feature analytics prompt context.
        recent_published = timezone.now() - timedelta(days=2)
        self.recent_a = create_post(
            self.tenant_a.workspace,
            social_account=self.account_a,
            caption="A-ONLY-RECENT high performer",
            published_at=recent_published,
        )
        self.recent_b = create_post(
            self.tenant_b.workspace,
            social_account=self.account_b,
            caption="B-SECRET-TENANT high performer",
            published_at=recent_published,
        )
        create_insight(
            self.recent_a,
            day=timezone.localdate(),
            views=2500,
            reach=1200,
            likes=240,
            comments=20,
            shares=10,
            saves=10,
        )
        create_insight(
            self.recent_b,
            day=timezone.localdate(),
            views=9000,
            reach=4000,
            likes=900,
            comments=100,
            shares=50,
            saves=50,
        )

        self.comment_a = create_comment(
            self.post_a, author_username="a_commenter", text="A comment"
        )
        self.comment_b = create_comment(
            self.post_b, author_username="b_commenter", text="B SECRET comment"
        )
        self.draft_a = create_draft(
            self.tenant_a.workspace, user=self.tenant_a.user, title="A draft"
        )
        self.draft_b = create_draft(
            self.tenant_b.workspace, user=self.tenant_b.user, title="B SECRET draft"
        )
        self.reel_a = create_reel_plan(
            self.tenant_a.workspace, user=self.tenant_a.user, title="A reel"
        )
        self.reel_b = create_reel_plan(
            self.tenant_b.workspace, user=self.tenant_b.user, title="B SECRET reel"
        )
        self.report_a = create_report(
            self.tenant_a.workspace, user=self.tenant_a.user, findings=["A finding"]
        )
        self.report_b = create_report(
            self.tenant_b.workspace, user=self.tenant_b.user, findings=["B SECRET finding"]
        )
        self.client_a = api_client_for(self.tenant_a)

    def test_list_endpoints_only_return_active_tenant(self):
        accounts = self.client_a.get("/api/v1/social-accounts/")
        self.assertEqual(accounts.status_code, 200)
        self.assertEqual(accounts.data["count"], 1)
        self.assertEqual(accounts.data["results"][0]["handle"], "@tenant_a")

        overview = self.client_a.get(
            "/api/v1/analytics/overview/?date_from=2026-02-01&date_to=2026-02-01"
        )
        self.assertEqual(overview.status_code, 200, overview.data)
        self.assertEqual(overview.data["totals"]["views"], 100)
        self.assertNotEqual(overview.data["totals"]["views"], 999)

        posts = self.client_a.get(
            "/api/v1/analytics/posts/?date_from=2026-02-01&date_to=2026-02-01"
        )
        self.assertEqual(posts.status_code, 200)
        self.assertEqual(posts.data["count"], 1)
        self.assertEqual(posts.data["results"][0]["id"], self.post_a.id)

        reports = self.client_a.get("/api/v1/analytics/reports/")
        self.assertEqual(reports.status_code, 200)
        self.assertEqual(reports.data["count"], 1)
        self.assertEqual(reports.data["results"][0]["id"], self.report_a.id)

        drafts = self.client_a.get("/api/v1/content/drafts/")
        self.assertEqual(drafts.status_code, 200)
        self.assertEqual(drafts.data["count"], 1)
        self.assertEqual(drafts.data["results"][0]["id"], self.draft_a.id)

        reels = self.client_a.get("/api/v1/reels/")
        self.assertEqual(reels.status_code, 200)
        self.assertEqual(reels.data["count"], 1)
        self.assertEqual(reels.data["results"][0]["id"], self.reel_a.id)

        comments = self.client_a.get("/api/v1/comments/")
        self.assertEqual(comments.status_code, 200)
        self.assertEqual(comments.data["count"], 1)
        self.assertEqual(comments.data["results"][0]["id"], self.comment_a.id)

    def test_guessed_foreign_ids_return_404_for_reads_updates_and_deletes(self):
        draft_url = f"/api/v1/content/drafts/{self.draft_b.id}/"
        reel_url = f"/api/v1/reels/{self.reel_b.id}/"
        report_url = f"/api/v1/analytics/reports/{self.report_b.id}/"

        for method, url, body in [
            ("get", draft_url, None),
            ("patch", draft_url, {"title": "hijacked"}),
            ("delete", draft_url, None),
            ("get", reel_url, None),
            ("patch", reel_url, {"title": "hijacked"}),
            ("delete", reel_url, None),
            ("get", report_url, None),
        ]:
            with self.subTest(method=method, url=url):
                response = getattr(self.client_a, method)(
                    url, body or {}, format="json"
                )
                self.assert_api_error(response, status_code=404, code="not_found")

        self.draft_b.refresh_from_db()
        self.reel_b.refresh_from_db()
        self.assertEqual(self.draft_b.title, "B SECRET draft")
        self.assertEqual(self.reel_b.title, "B SECRET reel")

    def test_foreign_workspace_header_is_rejected(self):
        client = api_client_for(self.tenant_a, workspace_id=self.tenant_b.workspace.id)
        response = client.get("/api/v1/analytics/overview/")
        self.assert_api_error(response, status_code=403, code="workspace_forbidden")

    def test_comment_analysis_with_foreign_comment_id_is_404_and_calls_no_ai(self):
        with mocked_ai() as ai:
            response = self.client_a.post(
                "/api/v1/comments/analyze/",
                {"comment_ids": [self.comment_a.id, self.comment_b.id]},
                format="json",
            )
            self.assert_api_error(response, status_code=404, code="not_found")
            self.assertEqual(ai.calls, [])
        self.comment_a.refresh_from_db()
        self.comment_b.refresh_from_db()
        self.assertEqual(self.comment_a.sentiment, "unknown")
        self.assertEqual(self.comment_b.sentiment, "unknown")

    def test_foreign_comment_reply_id_is_404_and_calls_no_ai(self):
        with mocked_ai() as ai:
            response = self.client_a.post(
                f"/api/v1/comments/{self.comment_b.id}/suggest-reply/",
                {},
                format="json",
            )
            self.assert_api_error(response, status_code=404, code="not_found")
            self.assertEqual(ai.calls, [])

    def test_client_cannot_inject_workspace_or_source_when_creating_draft(self):
        response = self.client_a.post(
            "/api/v1/content/drafts/",
            {
                "kind": "caption",
                "title": "My draft",
                "body": "body",
                "content": {"text": "caption"},
                "workspace": self.tenant_b.workspace.id,
                "created_by": self.tenant_b.user.id,
                "source": "ai",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        from apps.content_studio.models import ContentDraft

        draft = ContentDraft.objects.get(id=response.data["id"])
        self.assertEqual(draft.workspace_id, self.tenant_a.workspace.id)
        self.assertEqual(draft.created_by_id, self.tenant_a.user.id)
        self.assertEqual(draft.source, "manual")

    def test_generated_content_prompt_contains_only_active_tenant_context(self):
        with mocked_ai() as ai:
            response = self.client_a.post(
                "/api/v1/content/ideas/generate/",
                {"topic": "meal prep", "count": 2},
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(len(ai.calls), 1)
            prompt = ai.calls[0]["prompt"]
            self.assertIn("TENANT-A-NICHE", prompt)
            self.assertIn("A-ONLY-RECENT high performer", prompt)
            self.assertNotIn("B-SECRET-NICHE", prompt)
            self.assertNotIn("B-SECRET-TENANT", prompt)
            self.assertNotIn("B SECRET finding", prompt)

    def test_generated_draft_is_saved_in_active_tenant(self):
        with mocked_ai():
            response = self.client_a.post(
                "/api/v1/content/ideas/generate/",
                {"topic": "meal prep"},
                format="json",
            )
        self.assertEqual(response.status_code, 201, response.data)
        from apps.content_studio.models import ContentDraft

        draft = ContentDraft.objects.get(id=response.data["draft"]["id"])
        self.assertEqual(draft.workspace_id, self.tenant_a.workspace.id)
