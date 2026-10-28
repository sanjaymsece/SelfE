import logging
import os
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.comment_intelligence.models import Comment, CommentSentiment, CommentIntent
from apps.social_accounts.models import Post, SocialAccount
from apps.workspaces.models import Workspace

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class InstagramWebhookView(View):
    """
    Handles Meta (Instagram) Webhooks:
    - GET: Responds to Meta verification challenge (hub.challenge)
    - POST: Receives real-time Instagram comments and message events
    """

    def get(self, request, *args, **kwargs):
        verify_token = os.getenv("INSTAGRAM_WEBHOOK_VERIFY_TOKEN", "sociosync_meta_secret_2026")
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == verify_token:
            logger.info("Instagram Webhook verified successfully by Meta!")
            return HttpResponse(challenge, content_type="text/plain", status=200)

        logger.warning("Instagram Webhook verification failed: token mismatch")
        return HttpResponse("Verification token mismatch", status=403)

    def post(self, request, *args, **kwargs):
        import json
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        logger.info(f"Received Instagram webhook event: {payload.get('object')}")

        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                field = change.get("field")
                value = change.get("value", {})

                if field == "comments":
                    comment_id = value.get("id")
                    comment_text = value.get("text", "")
                    author = value.get("from", {}).get("username", "anonymous_user")
                    media_id = value.get("media", {}).get("id")

                    # Associate with post or workspace
                    post = Post.objects.filter(external_id=media_id).first()
                    workspace = post.workspace if post else Workspace.objects.first()

                    if workspace and post and comment_id:
                        Comment.objects.get_or_create(
                            external_id=str(comment_id),
                            defaults={
                                "workspace": workspace,
                                "post": post,
                                "author_username": author,
                                "text": comment_text,
                                "commented_at": timezone.now(),
                                "sentiment": CommentSentiment.POSITIVE if any(w in comment_text.lower() for w in ["love", "great", "best"]) else CommentSentiment.NEUTRAL,
                                "intent": CommentIntent.QUESTION if "?" in comment_text else CommentIntent.PRAISE,
                            },
                        )

        return JsonResponse({"status": "received"}, status=200)
