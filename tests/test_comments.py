from datetime import date

from django.utils import timezone

from ai.exceptions import AIProviderError, AIQuotaExceeded, AITimeout
from apps.comment_intelligence.models import Comment, CommentReplySuggestion
from apps.common.models import AIUsageLog
from tests.factories import (
    api_client_for,
    aware_datetime,
    create_comment,
    create_insight,
    create_post,
    create_social_account,
    create_tenant,
)
from tests.support import APIBaseTest, mocked_ai


def _analysis(comment_id, *, sentiment="positive", intent="praise"):
    return {
        "comment_id": comment_id,
        "sentiment": sentiment,
        "intent": intent,
        "is_question": intent == "question",
        "is_collaboration_opportunity": intent == "collaboration",
        "confidence": 0.91,
        "summary": "A concise simulated classification.",
    }


class CommentListTests(APIBaseTest):
    def setUp(self):
        self.tenant = create_tenant(email="comments-list@example.com")
        account = create_social_account(self.tenant.workspace)
        self.post_one = create_post(
            self.tenant.workspace,
            social_account=account,
            caption="How to store herbs",
            published_at=aware_datetime(2026, 3, 1, 9),
        )
        self.post_two = create_post(
            self.tenant.workspace,
            social_account=account,
            caption="A pantry restock",
            published_at=aware_datetime(2026, 3, 2, 9),
        )
        self.question = create_comment(
            self.post_one,
            author_username="curious_cook",
            text="How do I store coriander so it lasts?",
            commented_at=aware_datetime(2026, 3, 2, 10),
        )
        self.praise = create_comment(
            self.post_one,
            author_username="happy_eater",
            text="This storage tip was so useful!",
            commented_at=aware_datetime(2026, 3, 3, 10),
        )
        self.spam = create_comment(
            self.post_two,
            author_username="deal_bot",
            text="FREE FOLLOWERS click here",
            commented_at=aware_datetime(2026, 3, 4, 10),
        )
        Comment.objects.filter(pk=self.question.pk).update(
            sentiment="neutral",
            intent="question",
            is_question=True,
            confidence=0.88,
            analysis_summary="The author asks a storage question.",
            analyzed_at=timezone.now(),
        )
        Comment.objects.filter(pk=self.praise.pk).update(
            sentiment="positive",
            intent="praise",
            confidence=0.95,
            analysis_summary="The author gives specific praise.",
            analyzed_at=timezone.now(),
        )
        Comment.objects.filter(pk=self.spam.pk).update(
            sentiment="negative",
            intent="spam",
            confidence=0.99,
            analysis_summary="Promotional spam.",
            analyzed_at=timezone.now(),
        )
        self.client_a = api_client_for(self.tenant)

    def test_list_is_paginated_and_ordered_by_comment_time(self):
        response = self.client_a.get("/api/v1/comments/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [self.spam.id, self.praise.id, self.question.id],
        )
        self.assertEqual(
            response.data["results"][2]["post_caption"], "How to store herbs"
        )
        self.assertEqual(response.data["results"][2]["post"], self.post_one.id)

    def test_query_filters(self):
        cases = {
            "sentiment=positive": [self.praise.id],
            "intent=question": [self.question.id],
            f"post={self.post_two.id}": [self.spam.id],
            "is_question=true": [self.question.id],
            "analyzed=true": [self.spam.id, self.praise.id, self.question.id],
            "search=coriander": [self.question.id],
            "search=deal_bot": [self.spam.id],
        }
        for query, expected_ids in cases.items():
            with self.subTest(query=query):
                response = self.client_a.get(f"/api/v1/comments/?{query}")
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(
                    [item["id"] for item in response.data["results"]],
                    expected_ids,
                )

        unanalyzed = self.client_a.get("/api/v1/comments/?analyzed=false")
        self.assertEqual(unanalyzed.status_code, 200)
        self.assertEqual(unanalyzed.data["count"], 0)

    def test_invalid_filters_return_validation_error(self):
        for query, field in [
            ("sentiment=furious", "sentiment"),
            ("intent=broadcast", "intent"),
            ("post=not-an-int", "post"),
            ("is_question=maybe", "is_question"),
            ("analyzed=perhaps", "analyzed"),
        ]:
            with self.subTest(query=query):
                response = self.client_a.get(f"/api/v1/comments/?{query}")
                self.assert_api_error(
                    response, status_code=400, code="validation_error"
                )
                self.assertIn(field, response.data["error"]["details"])

    def test_post_filter_cannot_reveal_another_tenants_comments(self):
        other = create_tenant()
        other_post = create_post(other.workspace)
        create_comment(other_post, text="FOREIGN secret comment")
        response = self.client_a.get(
            f"/api/v1/comments/?post={other_post.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.assertNotIn(b"FOREIGN", response.content)


class CommentAnalysisTests(APIBaseTest):
    def setUp(self):
        self.tenant = create_tenant(
            email="comment-analysis@example.com",
            niche="herb gardening",
            tone="warm",
        )
        account = create_social_account(self.tenant.workspace)
        self.post = create_post(
            self.tenant.workspace,
            social_account=account,
            caption="A herb storage guide",
            published_at=aware_datetime(2026, 3, 1, 9),
        )
        create_insight(
            self.post,
            day=date(2026, 3, 1),
            views=1000,
            reach=500,
            likes=50,
        )
        self.question = create_comment(
            self.post,
            author_username="herb_helper",
            text="How long does this stay fresh?",
            commented_at=aware_datetime(2026, 3, 2, 10),
        )
        self.collab = create_comment(
            self.post,
            author_username="local_market",
            text="We would love to collaborate on a market stall.",
            commented_at=aware_datetime(2026, 3, 3, 10),
        )
        self.client_a = api_client_for(self.tenant)

    def test_analysis_persists_only_validated_classifications(self):
        response_payload = {
            "analyses": [
                _analysis(self.question.id, sentiment="neutral", intent="question"),
                _analysis(
                    self.collab.id,
                    sentiment="positive",
                    intent="collaboration",
                ),
            ]
        }
        with mocked_ai({"CommentAnalysisResult": response_payload}) as ai:
            response = self.client_a.post(
                "/api/v1/comments/analyze/",
                {"comment_ids": [self.question.id, self.collab.id]},
                format="json",
            )
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(len(ai.calls), 1)
            self.assertEqual(ai.calls[0]["schema"], "CommentAnalysisResult")
            prompt = ai.calls[0]["prompt"]
            self.assertIn("herb gardening", prompt)
            self.assertIn("How long does this stay fresh?", prompt)
            self.assertIn("We would love to collaborate", prompt)

        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["data_source"], "simulated")
        self.question.refresh_from_db()
        self.collab.refresh_from_db()
        self.assertEqual(self.question.sentiment, "neutral")
        self.assertEqual(self.question.intent, "question")
        self.assertTrue(self.question.is_question)
        self.assertEqual(self.question.confidence, 0.91)
        self.assertIsNotNone(self.question.analyzed_at)
        self.assertEqual(self.collab.intent, "collaboration")
        self.assertTrue(self.collab.is_collaboration_opportunity)
        self.assertFalse(self.collab.is_question)

        usage = AIUsageLog.objects.get(feature="comment_analysis")
        self.assertTrue(usage.success)
        self.assertEqual(usage.workspace_id, self.tenant.workspace.id)

    def test_without_ids_only_unanalyzed_comments_are_sent_to_ai(self):
        Comment.objects.filter(pk=self.collab.pk).update(
            sentiment="positive", intent="collaboration", analyzed_at=timezone.now()
        )
        with mocked_ai(
            {"CommentAnalysisResult": {"analyses": [_analysis(self.question.id)]}}
        ) as ai:
            response = self.client_a.post(
                "/api/v1/comments/analyze/", {}, format="json"
            )
            self.assertEqual(response.status_code, 200, response.data)
            prompt = ai.calls[0]["prompt"]
            self.assertIn("How long does this stay fresh?", prompt)
            self.assertNotIn("We would love to collaborate", prompt)

        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["analyzed"][0]["id"], self.question.id)

    def test_nothing_to_analyze_returns_400_without_calling_ai(self):
        Comment.objects.filter(workspace=self.tenant.workspace).update(
            analyzed_at=timezone.now()
        )
        with mocked_ai() as ai:
            response = self.client_a.post(
                "/api/v1/comments/analyze/", {}, format="json"
            )
            self.assertEqual(ai.calls, [])
        self.assert_api_error(
            response, status_code=400, code="no_comments_to_analyze"
        )

    def test_duplicate_or_empty_comment_ids_are_rejected_before_ai(self):
        for payload, field in [
            ({"comment_ids": [self.question.id, self.question.id]}, "comment_ids"),
            ({"comment_ids": []}, "comment_ids"),
            ({"comment_ids": list(range(1, 52))}, "comment_ids"),
        ]:
            with self.subTest(payload=payload):
                with mocked_ai() as ai:
                    response = self.client_a.post(
                        "/api/v1/comments/analyze/", payload, format="json"
                    )
                    self.assertEqual(ai.calls, [])
                self.assert_api_error(
                    response, status_code=400, code="validation_error"
                )
                self.assertIn(field, response.data["error"]["details"])

    def test_partial_ai_coverage_is_rejected_and_nothing_is_saved(self):
        with mocked_ai(
            {"CommentAnalysisResult": {"analyses": [_analysis(self.question.id)]}}
        ):
            response = self.client_a.post(
                "/api/v1/comments/analyze/",
                {"comment_ids": [self.question.id, self.collab.id]},
                format="json",
            )
        self.assert_api_error(
            response, status_code=502, code="ai_invalid_response"
        )
        self.question.refresh_from_db()
        self.collab.refresh_from_db()
        self.assertEqual(self.question.sentiment, "unknown")
        self.assertEqual(self.collab.sentiment, "unknown")
        self.assertIsNone(self.question.analyzed_at)
        usage = AIUsageLog.objects.get(feature="comment_analysis")
        self.assertFalse(usage.success)
        self.assertEqual(usage.error_kind, "ai_invalid_response")

    def test_schema_invalid_classification_is_rejected_and_nothing_is_saved(self):
        invalid = _analysis(self.question.id)
        invalid["sentiment"] = "furious"
        with mocked_ai(
            {
                "CommentAnalysisResult": {
                    "analyses": [invalid, _analysis(self.collab.id)]
                }
            }
        ):
            response = self.client_a.post(
                "/api/v1/comments/analyze/",
                {"comment_ids": [self.question.id, self.collab.id]},
                format="json",
            )
        self.assert_api_error(
            response, status_code=502, code="ai_invalid_response"
        )
        self.assertFalse(
            Comment.objects.filter(analyzed_at__isnull=False).exists()
        )

    def test_quota_failure_returns_429_and_does_not_mutate_comments(self):
        with mocked_ai(
            {"CommentAnalysisResult": AIQuotaExceeded("simulated quota")}
        ):
            response = self.client_a.post(
                "/api/v1/comments/analyze/",
                {"comment_ids": [self.question.id, self.collab.id]},
                format="json",
            )
        self.assert_api_error(response, status_code=429, code="ai_quota_exceeded")
        self.assertFalse(
            Comment.objects.filter(analyzed_at__isnull=False).exists()
        )
        self.assertEqual(CommentReplySuggestion.objects.count(), 0)


class CommentReplyTests(APIBaseTest):
    def setUp(self):
        self.tenant = create_tenant(
            email="comment-reply@example.com",
            niche="urban gardening",
            tone="warm",
            preferred_language="en",
        )
        account = create_social_account(self.tenant.workspace)
        self.post = create_post(
            self.tenant.workspace,
            social_account=account,
            caption="Balcony herbs for beginners",
            published_at=aware_datetime(2026, 3, 1, 9),
        )
        self.comment = create_comment(
            self.post,
            author_username="new_gardener",
            text="Can I grow basil on a north-facing balcony?",
            commented_at=aware_datetime(2026, 3, 2, 10),
        )
        Comment.objects.filter(pk=self.comment.pk).update(
            sentiment="neutral",
            intent="question",
            is_question=True,
            confidence=0.9,
            analyzed_at=timezone.now(),
        )
        self.comment.refresh_from_db()
        self.client_a = api_client_for(self.tenant)

    def test_successful_reply_generation_saves_history(self):
        with mocked_ai() as ai:
            response = self.client_a.post(
                f"/api/v1/comments/{self.comment.id}/suggest-reply/",
                {
                    "tone": "reassuring",
                    "language": "es",
                    "extra_instructions": "Mention that afternoon sun also works.",
                },
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(ai.calls[0]["schema"], "ReplySuggestionsResult")
            prompt = ai.calls[0]["prompt"]
            self.assertIn("Can I grow basil on a north-facing balcony?", prompt)
            self.assertIn("reassuring", prompt)
            self.assertIn("es", prompt)
            self.assertIn("Mention that afternoon sun also works.", prompt)
            self.assertIn("urban gardening", prompt)

        self.assertEqual(response.data["comment"], self.comment.id)
        self.assertGreaterEqual(len(response.data["suggestions"]), 1)
        self.assertEqual(response.data["tone"], "reassuring")
        self.assertTrue(response.data["model_used"])
        suggestion = CommentReplySuggestion.objects.get()
        self.assertEqual(suggestion.workspace_id, self.tenant.workspace.id)
        self.assertEqual(suggestion.created_by_id, self.tenant.user.id)
        self.assertEqual(suggestion.comment_id, self.comment.id)
        self.assertEqual(suggestion.tone, "reassuring")
        self.assertEqual(len(suggestion.suggestions), 1)

    def test_reply_defaults_to_saved_preferences(self):
        with mocked_ai() as ai:
            response = self.client_a.post(
                f"/api/v1/comments/{self.comment.id}/suggest-reply/",
                {},
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.data)
            prompt = ai.calls[0]["prompt"]
            self.assertIn("warm", prompt)
            self.assertIn("en", prompt)

        self.assertEqual(response.data["tone"], "warm")

    def test_invalid_ai_output_saves_no_suggestion(self):
        with mocked_ai({"ReplySuggestionsResult": {"suggestions": []}}):
            response = self.client_a.post(
                f"/api/v1/comments/{self.comment.id}/suggest-reply/",
                {},
                format="json",
            )
        self.assert_api_error(
            response, status_code=502, code="ai_invalid_response"
        )
        self.assertEqual(CommentReplySuggestion.objects.count(), 0)

    def test_provider_failure_saves_no_suggestion(self):
        with mocked_ai(
            {"ReplySuggestionsResult": AIProviderError("provider unavailable")}
        ):
            response = self.client_a.post(
                f"/api/v1/comments/{self.comment.id}/suggest-reply/",
                {},
                format="json",
            )
        self.assert_api_error(
            response, status_code=502, code="ai_provider_error"
        )
        self.assertEqual(CommentReplySuggestion.objects.count(), 0)

    def test_timeout_maps_to_504_and_saves_nothing(self):
        with mocked_ai({"ReplySuggestionsResult": AITimeout("timed out")}):
            response = self.client_a.post(
                f"/api/v1/comments/{self.comment.id}/suggest-reply/",
                {},
                format="json",
            )
        self.assert_api_error(response, status_code=504, code="ai_timeout")
        self.assertEqual(CommentReplySuggestion.objects.count(), 0)

    def test_invalid_reply_request_is_rejected_before_ai(self):
        with mocked_ai() as ai:
            response = self.client_a.post(
                f"/api/v1/comments/{self.comment.id}/suggest-reply/",
                {"extra_instructions": "x" * 501},
                format="json",
            )
            self.assertEqual(ai.calls, [])
        self.assert_api_error(response, status_code=400, code="validation_error")
        self.assertIn("extra_instructions", response.data["error"]["details"])
