from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
from django.test import SimpleTestCase, override_settings
from google.genai import errors as genai_errors
from pydantic import BaseModel

from ai.client import GeminiAIClient, get_ai_client
from ai.exceptions import (
    AINotConfigured,
    AIProviderError,
    AIQuotaExceeded,
    AITimeout,
    AIInvalidResponse,
)
from ai.schemas import AnalyticsExplanation


class ExampleResult(BaseModel):
    message: str


EXPLANATION = AnalyticsExplanation(
    summary="The supplied simulated metrics show steady engagement.",
    growth_explanation="The comparison is based only on the supplied totals.",
    key_findings=["The supplied totals are internally consistent."],
    recommendations=["Keep testing the supplied top-performing format."],
)


def _response(parsed=None, *, text=None, prompt_tokens=12, output_tokens=34):
    return SimpleNamespace(
        parsed=parsed,
        text=text,
        usage_metadata=SimpleNamespace(
            prompt_token_count=prompt_tokens,
            candidates_token_count=output_tokens,
        ),
        model_version="gemini-test-001",
    )


@override_settings(
    GEMINI_API_KEY="test-api-key",
    GEMINI_MODEL="gemini-test",
    GEMINI_MAX_ATTEMPTS=1,
    GEMINI_TIMEOUT_SECONDS=5,
)
class GeminiClientTests(SimpleTestCase):
    def make_client(self, sdk_client):
        with patch("google.genai.Client", return_value=sdk_client):
            return GeminiAIClient()

    def test_missing_api_key_and_model_fail_closed(self):
        with override_settings(GEMINI_API_KEY=""):
            with self.assertRaises(AINotConfigured):
                GeminiAIClient()
        with override_settings(GEMINI_MODEL=""):
            with self.assertRaises(AINotConfigured):
                GeminiAIClient()

    def test_parsed_pydantic_response_is_returned_with_usage(self):
        sdk = MagicMock()
        sdk.models.generate_content.return_value = _response(EXPLANATION)
        client = self.make_client(sdk)

        result = client.generate_structured(
            prompt="Explain the supplied metrics.",
            response_schema=AnalyticsExplanation,
            temperature=0.2,
        )

        self.assertEqual(result.data["summary"], EXPLANATION.summary)
        self.assertEqual(result.model, "gemini-test-001")
        self.assertEqual(result.prompt_tokens, 12)
        self.assertEqual(result.output_tokens, 34)
        call_kwargs = sdk.models.generate_content.call_args.kwargs
        self.assertEqual(call_kwargs["model"], "gemini-test")
        self.assertEqual(
            call_kwargs["config"].temperature,
            0.2,
        )
        self.assertEqual(
            call_kwargs["config"].response_mime_type, "application/json"
        )

    def test_parsed_dict_and_text_json_are_supported(self):
        sdk = MagicMock()
        sdk.models.generate_content.return_value = _response(
            {"message": "from a dictionary"}
        )
        result = self.make_client(sdk).generate_structured(
            prompt="Return a message.",
            response_schema=ExampleResult,
        )
        self.assertEqual(result.data, {"message": "from a dictionary"})

        sdk.models.generate_content.return_value = _response(
            None, text='{"message": "from json text"}'
        )
        result = self.make_client(sdk).generate_structured(
            prompt="Return a message.",
            response_schema=ExampleResult,
        )
        self.assertEqual(result.data, {"message": "from json text"})

    def test_missing_or_invalid_output_is_an_invalid_response(self):
        sdk = MagicMock()
        sdk.models.generate_content.return_value = _response(None, text="")
        with self.assertRaises(AIInvalidResponse):
            self.make_client(sdk).generate_structured(
                prompt="Return a message.", response_schema=ExampleResult
            )

        sdk.models.generate_content.return_value = _response(
            None, text="not valid json"
        )
        with self.assertRaises(AIInvalidResponse):
            self.make_client(sdk).generate_structured(
                prompt="Return a message.", response_schema=ExampleResult
            )

        sdk.models.generate_content.return_value = _response(
            {"unexpected": "shape"}
        )
        with self.assertRaises(AIInvalidResponse):
            self.make_client(sdk).generate_structured(
                prompt="Return a message.", response_schema=ExampleResult
            )

    def test_quota_error_maps_to_quota_exceeded(self):
        sdk = MagicMock()
        sdk.models.generate_content.side_effect = genai_errors.APIError(
            429, {"error": {"message": "quota", "status": "RESOURCE_EXHAUSTED"}}
        )
        with self.assertRaises(AIQuotaExceeded):
            self.make_client(sdk).generate_structured(
                prompt="Return a message.", response_schema=ExampleResult
            )

    def test_auth_and_model_errors_fail_as_not_configured(self):
        for code in (401, 403, 404):
            with self.subTest(code=code):
                sdk = MagicMock()
                sdk.models.generate_content.side_effect = genai_errors.APIError(
                    code, {"error": {"message": "denied", "status": "DENIED"}}
                )
                with self.assertRaises(AINotConfigured):
                    self.make_client(sdk).generate_structured(
                        prompt="Return a message.", response_schema=ExampleResult
                    )

    def test_server_and_client_api_errors_map_to_provider_error(self):
        for code in (400, 500, 503):
            with self.subTest(code=code):
                sdk = MagicMock()
                sdk.models.generate_content.side_effect = genai_errors.APIError(
                    code, {"error": {"message": "provider error"}}
                )
                with self.assertRaises(AIProviderError):
                    self.make_client(sdk).generate_structured(
                        prompt="Return a message.", response_schema=ExampleResult
                    )

    def test_timeout_and_transport_errors_are_mapped(self):
        sdk = MagicMock()
        sdk.models.generate_content.side_effect = httpx.ReadTimeout("too slow")
        with self.assertRaises(AITimeout):
            self.make_client(sdk).generate_structured(
                prompt="Return a message.", response_schema=ExampleResult
            )

        sdk.models.generate_content.side_effect = httpx.ConnectError("offline")
        with self.assertRaises(AIProviderError):
            self.make_client(sdk).generate_structured(
                prompt="Return a message.", response_schema=ExampleResult
            )

    def test_unexpected_provider_exception_is_sanitized(self):
        sdk = MagicMock()
        sdk.models.generate_content.side_effect = RuntimeError(
            "secret internal detail"
        )
        with self.assertRaises(AIProviderError) as caught:
            self.make_client(sdk).generate_structured(
                prompt="Return a message.", response_schema=ExampleResult
            )
        self.assertNotIn("secret internal detail", str(caught.exception))

    @override_settings(GEMINI_MAX_ATTEMPTS=2)
    def test_transient_server_error_is_retried_once(self):
        sdk = MagicMock()
        sdk.models.generate_content.side_effect = [
            genai_errors.APIError(503, {"error": {"message": "temporary"}}),
            _response({"message": "recovered"}),
        ]
        with patch("ai.client.time.sleep") as sleep:
            result = self.make_client(sdk).generate_structured(
                prompt="Return a message.", response_schema=ExampleResult
            )
        self.assertEqual(result.data, {"message": "recovered"})
        self.assertEqual(sdk.models.generate_content.call_count, 2)
        sleep.assert_called_once()

    @override_settings(GEMINI_MAX_ATTEMPTS=2)
    def test_exhausted_retries_raise_last_error(self):
        sdk = MagicMock()
        sdk.models.generate_content.side_effect = genai_errors.APIError(
            503, {"error": {"message": "temporary"}}
        )
        with patch("ai.client.time.sleep"):
            with self.assertRaises(AIProviderError):
                self.make_client(sdk).generate_structured(
                    prompt="Return a message.", response_schema=ExampleResult
                )
        self.assertEqual(sdk.models.generate_content.call_count, 2)

    def test_empty_or_oversized_prompt_is_rejected_before_provider_call(self):
        sdk = MagicMock()
        client = self.make_client(sdk)
        with self.assertRaises(AIProviderError):
            client.generate_structured(
                prompt="", response_schema=ExampleResult
            )
        with self.assertRaises(AIProviderError):
            client.generate_structured(
                prompt="x" * 60001, response_schema=ExampleResult
            )
        sdk.models.generate_content.assert_not_called()


class AIClientFactoryTests(SimpleTestCase):
    @override_settings(GEMINI_API_KEY="")
    def test_factory_does_not_fallback_when_provider_is_unconfigured(self):
        with self.assertRaises(AINotConfigured):
            get_ai_client()

    @override_settings(AI_CLIENT_CLASS="missing.module.Client")
    def test_factory_rejects_unimportable_client_class(self):
        with self.assertRaises(AINotConfigured):
            get_ai_client()
