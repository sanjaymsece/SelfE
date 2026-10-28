from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.comment_intelligence.models import Comment, CommentSentiment
from apps.social_accounts.models import Post, SocialAccount, SocialPlatform
from apps.workspaces.models import MembershipRole, Workspace, WorkspaceMembership


class WorkspaceAndFeatureExtensionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="StrongPassword123!",
            full_name="Owner User",
        )
        self.workspace = Workspace.objects.create(
            name="Workspace One",
            slug="workspace-one",
            niche="Fitness",
            timezone="UTC",
            created_by=self.user,
        )
        self.membership = WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.user,
            role=MembershipRole.OWNER,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_workspaces(self):
        response = self.client.get("/api/v1/workspaces/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Workspace One")

    def test_create_workspace(self):
        payload = {
            "name": "Workspace Two",
            "niche": "Tech",
            "timezone": "America/New_York",
        }
        response = self.client.post("/api/v1/workspaces/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Workspace Two")
        self.assertTrue(Workspace.objects.filter(name="Workspace Two").exists())

    def test_connect_and_disconnect_social_account(self):
        headers = {"HTTP_X_WORKSPACE_ID": str(self.workspace.id)}
        payload = {
            "platform": "instagram",
            "handle": "my_brand",
            "display_name": "My Brand",
            "follower_count": 1500,
        }
        create_res = self.client.post(
            "/api/v1/social-accounts/", payload, format="json", **headers
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        account_id = create_res.data["id"]

        list_res = self.client.get("/api/v1/social-accounts/", **headers)
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(list_res.data["count"], 1)
        self.assertEqual(list_res.data["results"][0]["handle"], "my_brand")

        delete_res = self.client.delete(
            f"/api/v1/social-accounts/{account_id}/", **headers
        )
        self.assertEqual(delete_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SocialAccount.objects.filter(id=account_id).exists())

    def test_comment_detail_and_update(self):
        from django.utils import timezone

        social_acc = SocialAccount.objects.create(
            workspace=self.workspace,
            platform=SocialPlatform.INSTAGRAM,
            handle="test_handle",
        )
        post = Post.objects.create(
            workspace=self.workspace,
            social_account=social_acc,
            external_id="post_ext_1",
            published_at=timezone.now(),
        )
        comment = Comment.objects.create(
            workspace=self.workspace,
            post=post,
            external_id="comm_ext_1",
            author_username="john_doe",
            text="Loved this workout!",
            commented_at=timezone.now(),
            sentiment=CommentSentiment.POSITIVE,
        )

        headers = {"HTTP_X_WORKSPACE_ID": str(self.workspace.id)}
        get_res = self.client.get(f"/api/v1/comments/{comment.id}/", **headers)
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data["author_username"], "john_doe")

        patch_res = self.client.patch(
            f"/api/v1/comments/{comment.id}/",
            {"sentiment": "positive", "is_collaboration_opportunity": True},
            format="json",
            **headers,
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertTrue(comment.is_collaboration_opportunity)
