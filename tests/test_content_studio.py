from datetime import timedelta

from django.test import override_settings
from django.utils import timezone

from ai.exceptions import AIProviderError, AIQuotaExceeded
from apps.common.models import AIUsageLog
from apps.content_studio.models import ContentDraft
from tests.factories import (
    api_client_for,
    create_draft,
    create_insight,
    create_post,
    create_report,
    create_social_account,
    create_tenant,
)
from tests.support import APIBaseTest, mocked_ai


class ContentStudioTests(APIBaseTest):
    def setUp(self):
        self.tenant = create_tenant(
            email="content@example.com",
            niche="sustainable meal prep",
            tone="playful",
            target_audience="busy students",
        )
        self.account = create_social_account(self.tenant.workspace)
        self.recent_post = create_post(
            self.tenant.workspace,
            social_account=self.account,
            caption="A recent top-performing meal prep post",
            published_at=timezone.now() - timedelta(days=2),
        )
        create_insight(
            self.recent_post,
            day=timezone.localdate(),
            views=2500,
            reach=1200,
            likes=240,
            comments=20,
            shares=10,
            saves=10,
        )
        create_report(
            self.tenant.workspace,
            user=self.tenant.user,
            findings=["A-ANALYTICS-FINDING for content strategy"],
        )
        self.client_a = api_client_for(self.tenant)

    def test_generate_ideas_uses_preferences_and_analytics_context(self):
        with mocked_ai() as ai:
            response = self.client_a.post(
                "/api/v1/content/ideas/generate/",
                {
                    "topic": "cheap protein bowls",
                    "platform": "instagram",
                    "count": 3,
                    "extra_instructions": "Avoid diet culture language.",
                },
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(len(ai.calls), 1)
            prompt = ai.calls[0]["prompt"]
            self.assertIn("sustainable meal prep", prompt)
            self.assertIn("playful", prompt)
            self.assertIn("A-ANALYTICS-FINDING for content strategy", prompt)
            self.assertIn("A recent top-performing meal prep post", prompt)
            self.assertIn("cheap protein bowls", prompt)

        self.assertEqual(response.data["data_source"], "simulated")
        self.assertEqual(response.data["draft"]["kind"], "idea")
        self.assertEqual(response.data["draft"]["source"], "ai")
        self.assertTrue(response.data["ideas"])
        draft = ContentDraft.objects.get(id=response.data["draft"]["id"])
        self.assertEqual(draft.workspace_id, self.tenant.workspace.id)
        self.assertEqual(draft.created_by_id, self.tenant.user.id)
        self.assertEqual(draft.source, "ai")
        self.assertIn("ideas", draft.content)
        self.assertEqual(draft.prompt_context["analytics_window_days"], 30)

    def test_generate_captions_saves_caption_draft(self):
        with mocked_ai() as ai:
            response = self.client_a.post(
                "/api/v1/content/captions/generate/",
                {"topic": "pantry lunches", "count": 2},
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(ai.calls[0]["schema"], "CaptionsResult")
        draft = ContentDraft.objects.get(id=response.data["draft"]["id"])
        self.assertEqual(draft.kind, "caption")
        self.assertTrue(draft.body)
        self.assertIn("captions", response.data)

    def test_generate_scripts_saves_script_draft(self):
        with mocked_ai() as ai:
            response = self.client_a.post(
                "/api/v1/content/scripts/generate/",
                {"topic": "meal prep on a budget", "count": 1},
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(ai.calls[0]["schema"], "ScriptsResult")
        draft = ContentDraft.objects.get(id=response.data["draft"]["id"])
        self.assertEqual(draft.kind, "script")
        self.assertIn("scripts", response.data)

    def test_manual_draft_crud_and_filters(self):
        create_draft(
            self.tenant.workspace,
            user=self.tenant.user,
            kind="idea",
            title="Existing idea",
        )
        created = self.client_a.post(
            "/api/v1/content/drafts/",
            {
                "kind": "caption",
                "title": "Manual caption",
                "body": "A caption",
                "content": {"text": "A caption"},
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["source"], "manual")
        draft_id = created.data["id"]

        filtered = self.client_a.get("/api/v1/content/drafts/?kind=caption")
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(filtered.data["count"], 1)
        self.assertEqual(filtered.data["results"][0]["id"], draft_id)

        patched = self.client_a.patch(
            f"/api/v1/content/drafts/{draft_id}/",
            {"title": "Updated caption", "status": "approved"},
            format="json",
        )
        self.assertEqual(patched.status_code, 200, patched.data)
        self.assertEqual(patched.data["title"], "Updated caption")
        self.assertEqual(patched.data["status"], "approved")
        self.assertEqual(patched.data["source"], "manual")

        deleted = self.client_a.delete(f"/api/v1/content/drafts/{draft_id}/")
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(ContentDraft.objects.filter(id=draft_id).exists())
        missing = self.client_a.get(f"/api/v1/content/drafts/{draft_id}/")
        self.assert_api_error(missing, status_code=404, code="not_found")

    def test_manual_draft_requires_json_object_content(self):
        response = self.client_a.post(
            "/api/v1/content/drafts/",
            {
                "kind": "caption",
                "title": "Bad content",
                "body": "",
                "content": ["not", "an", "object"],
            },
            format="json",
        )
        self.assert_api_error(response, status_code=400, code="validation_error")
        self.assertIn("content", response.data["error"]["details"])

    def test_invalid_generation_requests_are_rejected(self):
        for payload, field in [
            ({"count": 0}, "count"),
            ({"count": 99}, "count"),
            ({"platform": "myspace"}, "platform"),
            ({"extra_instructions": "x" * 1001}, "extra_instructions"),
        ]:
            with self.subTest(field=field):
                response = self.client_a.post(
                    "/api/v1/content/ideas/generate/", payload, format="json"
                )
                self.assert_api_error(
                    response, status_code=400, code="validation_error"
                )
                self.assertIn(field, response.data["error"]["details"])

    def test_invalid_ai_output_is_rejected_and_not_saved(self):
        with mocked_ai({"ContentIdeasResult": {"ideas": []}}) as ai:
            response = self.client_a.post(
                "/api/v1/content/ideas/generate/",
                {"topic": "test"},
                format="json",
            )
            self.assertEqual(len(ai.calls), 1)
        self.assert_api_error(
            response, status_code=502, code="ai_invalid_response"
        )
        self.assertEqual(ContentDraft.objects.count(), 0)
        usage = AIUsageLog.objects.get(feature="content_ideas")
        self.assertFalse(usage.success)

    def test_ai_quota_failure_returns_429_and_saves_nothing(self):
        with mocked_ai({"ContentIdeasResult": AIQuotaExceeded("quota")}):
            response = self.client_a.post(
                "/api/v1/content/ideas/generate/", {"topic": "test"}, format="json"
            )
        self.assert_api_error(response, status_code=429, code="ai_quota_exceeded")
        self.assertEqual(ContentDraft.objects.count(), 0)

    def test_ai_provider_failure_returns_502_and_saves_nothing(self):
        with mocked_ai({"CaptionsResult": AIProviderError("provider down")}):
            response = self.client_a.post(
                "/api/v1/content/captions/generate/",
                {"topic": "test"},
                format="json",
            )
        self.assert_api_error(response, status_code=502, code="ai_provider_error")
        self.assertEqual(ContentDraft.objects.count(), 0)

    @override_settings(GEMINI_API_KEY="")
    def test_missing_ai_credentials_returns_503_and_saves_nothing(self):
        response = self.client_a.post(
            "/api/v1/content/ideas/generate/", {"topic": "test"}, format="json"
        )
        self.assert_api_error(response, status_code=503, code="ai_not_configured")
        self.assertEqual(ContentDraft.objects.count(), 0)
