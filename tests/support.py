from contextlib import contextmanager
from unittest.mock import patch

from django.test import TestCase

from ai.mock import MockAIClient


@contextmanager
def mocked_ai(responses=None):
    client = MockAIClient(responses=responses)
    with patch("ai.service.get_ai_client", return_value=client):
        yield client


class APIBaseTest(TestCase):
    def assert_api_error(self, response, *, status_code, code):
        self.assertEqual(response.status_code, status_code, response.data)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], code)
        self.assertIn("message", response.data["error"])

    def assert_error_envelope(self, response):
        self.assertIn("error", response.data)
        self.assertIn("code", response.data["error"])
        self.assertIn("message", response.data["error"])
