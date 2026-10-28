from datetime import timedelta

from django.test import override_settings
from django.utils import timezone

from ai.exceptions import AIProviderError, AIQuotaExceeded
from apps.reel_generator.models import ReelPlan
from tests.factories import (
    api_client_for,
    create_insight,
    create_post,
    create_report,
    create_social_account,
    create_tenant,
)
from tests.support import APIBaseTest, mocked_ai


class ReelGeneratorTests(APIBaseTest):
    def setUp(self):
        self.tenant = create_tenant(
            email="reels@example.com",
            niche="strength coaching",
            tone="direct",
            target_audience="busy professionals",
        )
        self.account = create_social_account(self.tenant.workspace)
        post = create_post(
            self.tenant.workspace,
            social_account=self.account,
            caption="A recent strength training post",
            published_at=timezone.now() - timedelta(days=2),
        )
        create_insight(
            post,
            day=timezone.localdate(),
            views=3000,
            reach=1200,
            likes=300,
            comments=30,
            shares=20,
            saves=20,
        )
        create_report(
            self.tenant.workspace,
            user=self.tenant.user,
            findings=["REEL-ANALYTICS-FINDING"],
        )
        self.client_a = api_client_for(self.tenant)

    def test_generate_reel_saves_validated_plan(self):
        with mocked_ai() as ai:
            response = self.client_a.post(
                "/api/v1/reels/generate/",
                {
                    "topic": "three lifts for busy professionals",
                    "platform": "instagram",
                    "duration_seconds": 30,
                    "style": "documentary",
                },
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(len(ai.calls), 1)
            self.assertEqual(ai.calls[0]["schema"], "ReelPlanResult")
            prompt = ai.calls[0]["prompt"]
            self.assertIn("strength coaching", prompt)
            self.assertIn("REEL-ANALYTICS-FINDING", prompt)
            self.assertIn("three lifts for busy professionals", prompt)

        self.assertEqual(response.data["title"], "Three swaps, one cheaper grocery basket")
        self.assertEqual(response.data["target_duration_seconds"], 30)
        self.assertEqual(len(response.data["plan"]["scenes"]), 3)
        self.assertTrue(response.data["plan"]["hook"])
        self.assertTrue(response.data["plan"]["music_suggestion"])
        self.assertTrue(response.data["plan"]["call_to_action"])
        self.assertTrue(response.data["plan"]["scenes"][0]["camera_angle"])
        plan = ReelPlan.objects.get(id=response.data["id"])
        self.assertEqual(plan.workspace_id, self.tenant.workspace.id)
        self.assertEqual(plan.created_by_id, self.tenant.user.id)
        self.assertEqual(plan.status, "draft")

    def test_manual_reel_plan_create_uses_workspace_and_validates_schema(self):
        with mocked_ai():
            generated = self.client_a.post(
                "/api/v1/reels/generate/",
                {"topic": "source plan", "duration_seconds": 30},
                format="json",
            )
        plan = generated.data["plan"]

        created = self.client_a.post(
            "/api/v1/reels/",
            {
                "title": "Manually supplied plan",
                "topic": "manual plan topic",
                "platform": "instagram",
                "target_duration_seconds": 30,
                "status": "approved",
                "notes": "Ready for review.",
                "plan": plan,
                "workspace": self.tenant.workspace.id + 999,
                "created_by": self.tenant.user.id + 999,
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["title"], "Manually supplied plan")
        self.assertEqual(created.data["status"], "approved")
        self.assertEqual(created.data["plan"]["scenes"], plan["scenes"])
        saved = ReelPlan.objects.get(id=created.data["id"])
        self.assertEqual(saved.workspace_id, self.tenant.workspace.id)
        self.assertEqual(saved.created_by_id, self.tenant.user.id)

        invalid = self.client_a.post(
            "/api/v1/reels/",
            {
                "title": "Incomplete plan",
                "topic": "invalid",
                "target_duration_seconds": 30,
                "plan": {"title": "too little"},
            },
            format="json",
        )
        self.assert_api_error(invalid, status_code=400, code="validation_error")
        self.assertIn("plan", invalid.data["error"]["details"])

    def test_list_detail_update_and_delete(self):
        with mocked_ai():
            created = self.client_a.post(
                "/api/v1/reels/generate/",
                {"topic": "test reel", "duration_seconds": 30},
                format="json",
            )
        reel_id = created.data["id"]
        listing = self.client_a.get("/api/v1/reels/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data["count"], 1)

        detail = self.client_a.get(f"/api/v1/reels/{reel_id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["id"], reel_id)

        patched = self.client_a.patch(
            f"/api/v1/reels/{reel_id}/",
            {"title": "Approved reel", "status": "approved", "notes": "Ready to film."},
            format="json",
        )
        self.assertEqual(patched.status_code, 200, patched.data)
        self.assertEqual(patched.data["title"], "Approved reel")
        self.assertEqual(patched.data["status"], "approved")
        self.assertEqual(patched.data["notes"], "Ready to film.")

        deleted = self.client_a.delete(f"/api/v1/reels/{reel_id}/")
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(ReelPlan.objects.filter(id=reel_id).exists())

    def test_invalid_generation_request_is_rejected(self):
        short_topic = self.client_a.post(
            "/api/v1/reels/generate/", {"topic": "x"}, format="json"
        )
        self.assert_api_error(short_topic, status_code=400, code="validation_error")
        self.assertIn("topic", short_topic.data["error"]["details"])

        bad_duration = self.client_a.post(
            "/api/v1/reels/generate/",
            {"topic": "valid topic", "duration_seconds": 10},
            format="json",
        )
        self.assert_api_error(bad_duration, status_code=400, code="validation_error")
        self.assertIn("duration_seconds", bad_duration.data["error"]["details"])

    def test_invalid_ai_output_is_rejected_and_not_saved(self):
        with mocked_ai({"ReelPlanResult": {"title": "incomplete"}}):
            response = self.client_a.post(
                "/api/v1/reels/generate/",
                {"topic": "valid topic", "duration_seconds": 30},
                format="json",
            )
        self.assert_api_error(
            response, status_code=502, code="ai_invalid_response"
        )
        self.assertEqual(ReelPlan.objects.count(), 0)

    def test_ai_quota_failure_returns_429_and_saves_nothing(self):
        with mocked_ai({"ReelPlanResult": AIQuotaExceeded("quota")}):
            response = self.client_a.post(
                "/api/v1/reels/generate/",
                {"topic": "valid topic", "duration_seconds": 30},
                format="json",
            )
        self.assert_api_error(response, status_code=429, code="ai_quota_exceeded")
        self.assertEqual(ReelPlan.objects.count(), 0)

    def test_ai_provider_failure_returns_502_and_saves_nothing(self):
        with mocked_ai({"ReelPlanResult": AIProviderError("provider down")}):
            response = self.client_a.post(
                "/api/v1/reels/generate/",
                {"topic": "valid topic", "duration_seconds": 30},
                format="json",
            )
        self.assert_api_error(response, status_code=502, code="ai_provider_error")
        self.assertEqual(ReelPlan.objects.count(), 0)

    @override_settings(GEMINI_API_KEY="")
    def test_missing_ai_credentials_returns_503(self):
        response = self.client_a.post(
            "/api/v1/reels/generate/",
            {"topic": "valid topic", "duration_seconds": 30},
            format="json",
        )
        self.assert_api_error(response, status_code=503, code="ai_not_configured")
        self.assertEqual(ReelPlan.objects.count(), 0)
