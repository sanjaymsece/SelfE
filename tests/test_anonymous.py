from tests.support import APIBaseTest


class AnonymousAccessTests(APIBaseTest):
    protected_requests = [
        ("get", "/api/v1/auth/me/", None),
        ("get", "/api/v1/auth/preferences/", None),
        ("patch", "/api/v1/auth/preferences/", {"tone": "warm"}),
        ("get", "/api/v1/social-accounts/", None),
        ("get", "/api/v1/analytics/overview/", None),
        ("get", "/api/v1/analytics/posts/", None),
        ("get", "/api/v1/analytics/reports/", None),
        ("post", "/api/v1/analytics/reports/generate/", {}),
        ("get", "/api/v1/analytics/posting-times/", None),
        ("post", "/api/v1/content/ideas/generate/", {}),
        ("post", "/api/v1/content/captions/generate/", {}),
        ("post", "/api/v1/content/scripts/generate/", {}),
        ("get", "/api/v1/content/drafts/", None),
        ("post", "/api/v1/content/drafts/", {}),
        ("post", "/api/v1/reels/generate/", {}),
        ("get", "/api/v1/reels/", None),
        ("post", "/api/v1/reels/", {}),
        ("get", "/api/v1/comments/", None),
        ("post", "/api/v1/comments/analyze/", {}),
        ("post", "/api/v1/comments/1/suggest-reply/", {}),
    ]

    def test_all_protected_endpoints_reject_anonymous_requests(self):
        for method, path, body in self.protected_requests:
            with self.subTest(method=method, path=path):
                response = getattr(self.client, method)(
                    path, body or {}, format="json"
                )
                self.assert_api_error(
                    response, status_code=401, code="not_authenticated"
                )
                self.assertIn("WWW-Authenticate", response.headers)

    def test_public_health_and_docs_are_reachable(self):
        health = self.client.get("/api/v1/health/")
        self.assertEqual(health.status_code, 200, health.data)
        self.assertNotIn("GEMINI_API_KEY", health.content.decode())

        schema = self.client.get("/api/v1/schema/")
        self.assertEqual(schema.status_code, 200)
        docs = self.client.get("/api/v1/docs/")
        self.assertEqual(docs.status_code, 200)
