from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import UserPreference
from apps.workspaces.models import WorkspaceMembership
from tests.factories import (
    TEST_PASSWORD,
    add_workspace_membership,
    create_tenant,
)
from tests.support import APIBaseTest

User = get_user_model()


class RegistrationTests(APIBaseTest):
    def test_registration_creates_user_workspace_membership_and_preferences(self):
        payload = {
            "email": "new.user@example.com",
            "password": "StrongPass123!",
            "full_name": "New User",
            "workspace_name": "New Studio",
            "niche": "sustainable fashion",
            "goals": ["grow reach", "launch a newsletter"],
            "preferred_language": "en",
            "tone": "warm",
            "content_style": "educational",
            "target_audience": "conscious shoppers",
        }
        response = self.client.post("/api/v1/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["token_type"], "Bearer")
        self.assertEqual(response.data["workspace"]["name"], "New Studio")

        user = User.objects.get(email="new.user@example.com")
        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertNotEqual(user.password, "StrongPass123!")
        self.assertTrue(
            WorkspaceMembership.objects.filter(
                user=user, workspace_id=response.data["workspace"]["id"], role="owner"
            ).exists()
        )
        preference = UserPreference.objects.get(user=user)
        self.assertEqual(preference.niche, "sustainable fashion")
        self.assertEqual(preference.goals, ["grow reach", "launch a newsletter"])

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        me = client.get("/api/v1/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["email"], "new.user@example.com")
        self.assertEqual(len(me.data["workspaces"]), 1)

    def test_duplicate_email_is_case_insensitive(self):
        first = {
            "email": "duplicate@example.com",
            "password": "StrongPass123!",
            "workspace_name": "First",
        }
        response = self.client.post("/api/v1/auth/register/", first, format="json")
        self.assertEqual(response.status_code, 201)
        duplicate = {
            "email": "DUPLICATE@example.com",
            "password": "StrongPass123!",
            "workspace_name": "Second",
        }
        response = self.client.post("/api/v1/auth/register/", duplicate, format="json")
        self.assert_api_error(response, status_code=400, code="validation_error")
        self.assertIn("email", response.data["error"]["details"])
        self.assertEqual(User.objects.filter(email__iexact="duplicate@example.com").count(), 1)

    def test_weak_password_is_rejected(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "weak@example.com",
                "password": "short",
                "workspace_name": "Weak",
            },
            format="json",
        )
        self.assert_api_error(response, status_code=400, code="validation_error")
        self.assertIn("password", response.data["error"]["details"])
        self.assertFalse(User.objects.filter(email="weak@example.com").exists())

    def test_missing_fields_returns_validation_envelope(self):
        response = self.client.post("/api/v1/auth/register/", {}, format="json")
        self.assert_api_error(response, status_code=400, code="validation_error")
        self.assertIn("email", response.data["error"]["details"])
        self.assertIn("password", response.data["error"]["details"])


class LoginAndJWTTests(APIBaseTest):
    def setUp(self):
        self.tenant = create_tenant(email="login@example.com")

    def test_login_returns_jwt_and_token_works(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "LOGIN@example.com", "password": TEST_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        me = client.get("/api/v1/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["id"], self.tenant.user.id)
        self.assertEqual(me.data["workspaces"][0]["role"], "owner")

    def test_wrong_password_returns_generic_401(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "login@example.com", "password": "NotThePassword!"},
            format="json",
        )
        self.assert_api_error(response, status_code=401, code="authentication_failed")
        self.assertNotIn("login@example.com", response.data["error"]["message"])

    def test_unknown_email_returns_same_generic_error(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "nobody@example.com", "password": "WhateverPass123!"},
            format="json",
        )
        self.assert_api_error(response, status_code=401, code="authentication_failed")

    def test_refresh_endpoint_returns_new_access_token(self):
        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "login@example.com", "password": TEST_PASSWORD},
            format="json",
        )
        refresh = login.data["refresh"]
        response = self.client.post(
            "/api/v1/auth/refresh/", {"refresh": refresh}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("access", response.data)

    def test_preferences_can_be_retrieved_and_updated(self):
        client = APIClient()
        client.force_authenticate(user=self.tenant.user)
        get_response = client.get("/api/v1/auth/preferences/")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.data["niche"], "plant-based cooking")

        patch_response = client.patch(
            "/api/v1/auth/preferences/",
            {
                "niche": "budget vegan recipes",
                "goals": ["increase saves", "build a community"],
                "tone": "playful",
                "preferred_language": "es",
                "target_audience": "students",
                "keywords": ["budget", "quick meals"],
            },
            format="json",
        )
        self.assertEqual(patch_response.status_code, 200, patch_response.data)
        self.tenant.preference.refresh_from_db()
        self.assertEqual(self.tenant.preference.niche, "budget vegan recipes")
        self.assertEqual(self.tenant.preference.tone, "playful")
        self.assertEqual(self.tenant.preference.preferred_language, "es")

    def test_preferences_are_isolated_between_users(self):
        other = create_tenant(niche="a completely different niche")
        client = APIClient()
        client.force_authenticate(user=other.user)
        response = client.get("/api/v1/auth/preferences/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["niche"], "a completely different niche")
        self.assertNotEqual(response.data["niche"], self.tenant.preference.niche)


class WorkspaceSelectionTests(APIBaseTest):
    def setUp(self):
        self.tenant = create_tenant(email="multi@example.com")
        self.second_workspace = add_workspace_membership(
            self.tenant.user, "Second Workspace"
        )
        self.other_tenant = create_tenant()

    def test_multiple_workspaces_require_header(self):
        client = APIClient()
        client.force_authenticate(user=self.tenant.user)
        response = client.get("/api/v1/social-accounts/")
        self.assert_api_error(response, status_code=400, code="workspace_required")

    def test_header_selects_authorized_workspace(self):
        client = APIClient()
        client.force_authenticate(user=self.tenant.user)
        client.credentials(HTTP_X_WORKSPACE_ID=str(self.second_workspace.id))
        response = client.get("/api/v1/social-accounts/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 0)

    def test_header_for_foreign_workspace_is_forbidden(self):
        client = APIClient()
        client.force_authenticate(user=self.tenant.user)
        client.credentials(HTTP_X_WORKSPACE_ID=str(self.other_tenant.workspace.id))
        response = client.get("/api/v1/social-accounts/")
        self.assert_api_error(response, status_code=403, code="workspace_forbidden")

    def test_invalid_workspace_header_returns_400(self):
        client = APIClient()
        client.force_authenticate(user=self.tenant.user)
        client.credentials(HTTP_X_WORKSPACE_ID="not-an-id")
        response = client.get("/api/v1/social-accounts/")
        self.assert_api_error(response, status_code=400, code="invalid_workspace")

    def test_user_without_membership_has_no_workspace(self):
        orphan = create_tenant()
        WorkspaceMembership.objects.filter(user=orphan.user).delete()
        client = APIClient()
        client.force_authenticate(user=orphan.user)
        response = client.get("/api/v1/social-accounts/")
        self.assert_api_error(response, status_code=403, code="no_workspace")
