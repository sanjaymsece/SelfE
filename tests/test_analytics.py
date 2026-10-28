from datetime import date, datetime, timezone as dt_timezone

from django.test import override_settings

from ai.exceptions import AIQuotaExceeded
from apps.analytics.models import AnalyticsReport
from apps.common.models import AIUsageLog
from tests.factories import (
    api_client_for,
    create_insight,
    create_post,
    create_social_account,
    create_tenant,
)
from tests.support import APIBaseTest, mocked_ai


class AnalyticsCalculationTests(APIBaseTest):
    def setUp(self):
        self.tenant = create_tenant(email="analytics@example.com")
        self.account = create_social_account(self.tenant.workspace)
        self.post_one = create_post(
            self.tenant.workspace,
            social_account=self.account,
            caption="Post one",
            media_type="carousel",
            published_at=datetime(2026, 3, 8, 9, tzinfo=dt_timezone.utc),
        )
        self.post_two = create_post(
            self.tenant.workspace,
            social_account=self.account,
            caption="Post two",
            media_type="reel",
            published_at=datetime(2026, 3, 10, 18, tzinfo=dt_timezone.utc),
        )
        create_insight(
            self.post_one,
            day=date(2026, 3, 8),
            views=1000,
            reach=500,
            likes=100,
            comments=20,
            shares=10,
            saves=5,
        )
        create_insight(
            self.post_one,
            day=date(2026, 3, 9),
            views=500,
            reach=250,
            likes=50,
            comments=10,
            shares=5,
            saves=5,
        )
        create_insight(
            self.post_two,
            day=date(2026, 3, 10),
            views=2000,
            reach=1000,
            likes=200,
            comments=0,
            shares=0,
            saves=0,
        )
        create_insight(
            self.post_one,
            day=date(2026, 3, 2),
            views=700,
            reach=350,
            likes=70,
            comments=7,
            shares=7,
            saves=7,
        )
        self.client_a = api_client_for(self.tenant)

    def test_overview_uses_known_fixture_metrics_and_prior_period(self):
        response = self.client_a.get(
            "/api/v1/analytics/overview/?date_from=2026-03-08&date_to=2026-03-14"
        )
        self.assertEqual(response.status_code, 200, response.data)
        totals = response.data["totals"]
        self.assertEqual(totals["views"], 3500)
        self.assertEqual(totals["reach"], 1750)
        self.assertEqual(totals["likes"], 350)
        self.assertEqual(totals["comments"], 30)
        self.assertEqual(totals["shares"], 15)
        self.assertEqual(totals["saves"], 10)
        self.assertEqual(totals["engagement"], 405)
        self.assertEqual(totals["engagement_rate"], 23.14)
        self.assertEqual(totals["reach_rate"], 50.0)
        self.assertEqual(totals["save_rate"], 0.57)
        self.assertEqual(totals["posts"], 2)

        previous = response.data["previous_totals"]
        self.assertEqual(previous["views"], 700)
        self.assertEqual(previous["reach"], 350)
        self.assertEqual(previous["engagement"], 91)
        self.assertEqual(previous["engagement_rate"], 26.0)
        self.assertEqual(previous["posts"], 1)

        growth = response.data["growth"]
        self.assertEqual(growth["views_pct"], 400.0)
        self.assertEqual(growth["engagement_pct"], 345.05)
        self.assertEqual(growth["comments_pct"], 328.57)
        self.assertEqual(growth["posts_pct"], 100.0)
        self.assertEqual(growth["engagement_rate_change_points"], -2.86)
        self.assertTrue(growth["has_prior_data"])

        self.assertEqual(
            response.data["comparison_period"],
            {"date_from": "2026-03-01", "date_to": "2026-03-07", "days": 7},
        )
        self.assertEqual(response.data["data_source"], "simulated")
        self.assertEqual(len(response.data["daily_series"]), 3)
        self.assertEqual(response.data["daily_series"][0]["engagement_rate"], 27.0)
        self.assertEqual(response.data["daily_series"][1]["engagement_rate"], 28.0)
        self.assertEqual(response.data["daily_series"][2]["engagement_rate"], 20.0)

    def test_top_posts_are_ranked_by_engagement_rate(self):
        response = self.client_a.get(
            "/api/v1/analytics/overview/?date_from=2026-03-08&date_to=2026-03-14"
        )
        top = response.data["top_posts"]
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0]["id"], self.post_one.id)
        self.assertEqual(top[0]["metrics"]["engagement"], 205)
        self.assertEqual(top[0]["metrics"]["engagement_rate"], 27.33)
        self.assertEqual(top[1]["id"], self.post_two.id)
        self.assertEqual(top[1]["metrics"]["engagement_rate"], 20.0)

    def test_posts_endpoint_filters_and_paginates(self):
        response = self.client_a.get(
            "/api/v1/analytics/posts/?date_from=2026-03-08&date_to=2026-03-14"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [self.post_one.id, self.post_two.id],
        )

        filtered = self.client_a.get(
            "/api/v1/analytics/posts/?date_from=2026-03-08&date_to=2026-03-14&media_type=reel"
        )
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(filtered.data["count"], 1)
        self.assertEqual(filtered.data["results"][0]["id"], self.post_two.id)

        invalid = self.client_a.get(
            "/api/v1/analytics/posts/?date_from=2026-03-08&date_to=2026-03-14&platform=myspace"
        )
        self.assert_api_error(invalid, status_code=400, code="validation_error")

    def test_invalid_or_oversized_date_range_is_rejected(self):
        reversed_range = self.client_a.get(
            "/api/v1/analytics/overview/?date_from=2026-03-14&date_to=2026-03-08"
        )
        self.assert_api_error(
            reversed_range, status_code=400, code="invalid_date_range"
        )

        oversized = self.client_a.get(
            "/api/v1/analytics/overview/?date_from=2020-01-01&date_to=2026-01-01"
        )
        self.assert_api_error(oversized, status_code=400, code="invalid_date_range")

    def test_empty_period_returns_zeroes_and_no_invented_trend(self):
        response = self.client_a.get(
            "/api/v1/analytics/overview/?date_from=2026-01-01&date_to=2026-01-07"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["has_data"])
        self.assertEqual(response.data["totals"]["views"], 0)
        self.assertFalse(response.data["growth"]["has_prior_data"])
        self.assertIsNone(response.data["growth"]["views_pct"])


class PostingTimeTests(APIBaseTest):
    def setUp(self):
        self.tenant = create_tenant(email="posting@example.com")
        self.account = create_social_account(self.tenant.workspace)
        self._post(
            "monday-a",
            datetime(2026, 3, 2, 9, tzinfo=dt_timezone.utc),
            100,
        )
        self._post(
            "monday-b",
            datetime(2026, 3, 9, 9, tzinfo=dt_timezone.utc),
            120,
        )
        self._post(
            "tuesday-a",
            datetime(2026, 3, 3, 18, tzinfo=dt_timezone.utc),
            200,
        )
        self._post(
            "tuesday-b",
            datetime(2026, 3, 10, 18, tzinfo=dt_timezone.utc),
            220,
        )
        self.client_a = api_client_for(self.tenant)

    def _post(self, external_id, published_at, likes):
        post = create_post(
            self.tenant.workspace,
            social_account=self.account,
            external_id=external_id,
            published_at=published_at,
        )
        create_insight(
            post,
            day=published_at.date(),
            views=2000,
            reach=1000,
            likes=likes,
            comments=0,
            shares=0,
            saves=0,
        )
        return post

    def test_known_slots_are_ranked_by_mean_post_engagement_rate(self):
        response = self.client_a.get(
            "/api/v1/analytics/posting-times/?date_from=2026-03-01&date_to=2026-03-31&min_posts=2"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["sample_posts"], 4)
        self.assertEqual(response.data["data_source"], "simulated")
        recommendations = response.data["recommendations"]
        self.assertEqual(len(recommendations), 2)
        first = recommendations[0]
        self.assertEqual(first["day_of_week"], 1)
        self.assertEqual(first["day_label"], "Tuesday")
        self.assertEqual(first["hour"], 18)
        self.assertEqual(first["hour_label"], "18:00")
        self.assertEqual(first["sample_size"], 2)
        self.assertEqual(first["avg_engagement_rate"], 21.0)
        self.assertEqual(first["total_engagement"], 420)
        self.assertEqual(first["average_engagement_per_post"], 210.0)
        self.assertEqual(first["confidence"], "low")
        self.assertEqual(recommendations[1]["day_label"], "Monday")
        self.assertEqual(recommendations[1]["avg_engagement_rate"], 11.0)

    def test_low_sample_fallback_is_explicit(self):
        response = self.client_a.get(
            "/api/v1/analytics/posting-times/?date_from=2026-03-01&date_to=2026-03-31&min_posts=10"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data["note"])
        self.assertEqual(len(response.data["recommendations"]), 2)

    def test_timezone_conversion_uses_workspace_timezone(self):
        local_tenant = create_tenant(
            email="timezone@example.com", timezone_name="America/New_York"
        )
        account = create_social_account(local_tenant.workspace)
        post = create_post(
            local_tenant.workspace,
            social_account=account,
            published_at=datetime(2026, 3, 2, 14, tzinfo=dt_timezone.utc),
        )
        create_insight(post, day=date(2026, 3, 2), views=1000, reach=500, likes=50)
        client = api_client_for(local_tenant)
        response = client.get(
            "/api/v1/analytics/posting-times/?date_from=2026-03-01&date_to=2026-03-31&min_posts=1"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["timezone"], "America/New_York")
        self.assertEqual(response.data["recommendations"][0]["day_label"], "Monday")
        self.assertEqual(response.data["recommendations"][0]["hour"], 9)

    def test_invalid_min_posts_is_rejected(self):
        response = self.client_a.get(
            "/api/v1/analytics/posting-times/?min_posts=0"
        )
        self.assert_api_error(response, status_code=400, code="validation_error")


class AnalyticsReportTests(APIBaseTest):
    def setUp(self):
        self.tenant = create_tenant(email="report@example.com")
        self.account = create_social_account(self.tenant.workspace)
        post = create_post(
            self.tenant.workspace,
            social_account=self.account,
            caption="Report source post",
            published_at=datetime(2026, 3, 8, 9, tzinfo=dt_timezone.utc),
        )
        create_insight(
            post,
            day=date(2026, 3, 8),
            views=1000,
            reach=500,
            likes=100,
            comments=20,
            shares=10,
            saves=5,
        )
        self.client_a = api_client_for(self.tenant)

    def test_generate_report_saves_calculated_metrics_and_validated_explanation(self):
        with mocked_ai() as ai:
            response = self.client_a.post(
                "/api/v1/analytics/reports/generate/",
                {"date_from": "2026-03-08", "date_to": "2026-03-14"},
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(len(ai.calls), 1)
            self.assertEqual(ai.calls[0]["schema"], "AnalyticsExplanation")
            self.assertIn('"current_totals"', ai.calls[0]["prompt"])

        report = AnalyticsReport.objects.get()
        self.assertEqual(report.workspace_id, self.tenant.workspace.id)
        self.assertEqual(report.metrics["totals"]["views"], 1000)
        self.assertEqual(report.metrics["totals"]["engagement"], 135)
        self.assertEqual(report.metrics["totals"]["engagement_rate"], 27.0)
        self.assertEqual(
            report.explanation["summary"],
            "The current period shows engagement across the simulated posts.",
        )
        self.assertTrue(
            AIUsageLog.objects.filter(
                workspace=self.tenant.workspace,
                feature="analytics_report",
                success=True,
            ).exists()
        )

    def test_ai_quota_failure_does_not_save_a_report(self):
        with mocked_ai(
            {"AnalyticsExplanation": AIQuotaExceeded("simulated quota exhaustion")}
        ):
            response = self.client_a.post(
                "/api/v1/analytics/reports/generate/",
                {"date_from": "2026-03-08", "date_to": "2026-03-14"},
                format="json",
            )
        self.assert_api_error(response, status_code=429, code="ai_quota_exceeded")
        self.assertEqual(AnalyticsReport.objects.count(), 0)
        usage = AIUsageLog.objects.get(feature="analytics_report")
        self.assertFalse(usage.success)
        self.assertEqual(usage.error_kind, "ai_quota_exceeded")

    def test_invalid_ai_output_does_not_save_a_report(self):
        with mocked_ai({"AnalyticsExplanation": {"summary": "too short"}}):
            response = self.client_a.post(
                "/api/v1/analytics/reports/generate/",
                {"date_from": "2026-03-08", "date_to": "2026-03-14"},
                format="json",
            )
        self.assert_api_error(
            response, status_code=502, code="ai_invalid_response"
        )
        self.assertEqual(AnalyticsReport.objects.count(), 0)

    @override_settings(GEMINI_API_KEY="")
    def test_missing_ai_credentials_fails_closed(self):
        response = self.client_a.post(
            "/api/v1/analytics/reports/generate/",
            {"date_from": "2026-03-08", "date_to": "2026-03-14"},
            format="json",
        )
        self.assert_api_error(response, status_code=503, code="ai_not_configured")
        self.assertEqual(AnalyticsReport.objects.count(), 0)

    def test_report_for_period_without_data_is_rejected(self):
        with mocked_ai() as ai:
            response = self.client_a.post(
                "/api/v1/analytics/reports/generate/",
                {"date_from": "2026-01-01", "date_to": "2026-01-07"},
                format="json",
            )
            self.assert_api_error(
                response, status_code=400, code="no_data_for_period"
            )
            self.assertEqual(ai.calls, [])
        self.assertEqual(AnalyticsReport.objects.count(), 0)

    def test_saved_reports_are_listed_and_retrievable(self):
        with mocked_ai():
            created = self.client_a.post(
                "/api/v1/analytics/reports/generate/",
                {"date_from": "2026-03-08", "date_to": "2026-03-14"},
                format="json",
            )
        report_id = created.data["id"]
        listing = self.client_a.get("/api/v1/analytics/reports/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data["count"], 1)
        detail = self.client_a.get(f"/api/v1/analytics/reports/{report_id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["id"], report_id)
