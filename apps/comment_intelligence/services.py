from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound

from ai.exceptions import AIInvalidResponse
from ai.prompts.comments import (
    build_comment_analysis_prompt,
    build_reply_prompt,
)
from ai.schemas import CommentAnalysisResult, ReplySuggestionsResult
from ai.service import generate_ai_structured
from apps.comment_intelligence.models import (
    Comment,
    CommentReplySuggestion,
)
from apps.common.exceptions import NoCommentsToAnalyze
from apps.workspaces.services import build_brand_profile

MAX_COMMENTS_PER_ANALYSIS = 50


def _comment_prompt_item(comment: Comment) -> dict:
    return {
        "comment_id": comment.id,
        "author_username": comment.author_username,
        "text": comment.text[:2000],
        "liked_by": comment.like_count,
        "post_id": comment.post_id,
        "post_caption": (comment.post.caption or "")[:400],
        "post_media_type": comment.post.media_type,
    }


def comments_for_analysis(workspace, comment_ids=None):
    if comment_ids is not None:
        comments = list(
            Comment.objects.filter(workspace=workspace, id__in=comment_ids)
            .select_related("post")
            .order_by("commented_at", "id")
        )
        if len(comments) != len(set(comment_ids)):
            # Deliberately generic: do not confirm whether another tenant's ID exists.
            raise NotFound("One or more comments were not found.")
        return comments

    comments = list(
        Comment.objects.filter(workspace=workspace, analyzed_at__isnull=True)
        .select_related("post")
        .order_by("commented_at", "id")[:MAX_COMMENTS_PER_ANALYSIS]
    )
    if not comments:
        raise NoCommentsToAnalyze()
    return comments


def analyze_comments(*, workspace, user, comment_ids=None):
    comments = comments_for_analysis(workspace, comment_ids)
    expected_ids = {comment.id for comment in comments}
    brand_profile = build_brand_profile(user, workspace)

    def validate_ids(parsed: CommentAnalysisResult):
        returned_ids = [item.comment_id for item in parsed.analyses]
        if len(returned_ids) != len(set(returned_ids)) or set(returned_ids) != expected_ids:
            raise AIInvalidResponse(
                "AI analysis did not classify exactly the requested comments."
            )

    parsed = generate_ai_structured(
        feature="comment_analysis",
        workspace=workspace,
        user=user,
        prompt=build_comment_analysis_prompt(
            comments=[_comment_prompt_item(comment) for comment in comments],
            brand_profile=brand_profile,
        ),
        response_schema=CommentAnalysisResult,
        temperature=0.1,
        validator=validate_ids,
    )

    by_id = {item.comment_id: item for item in parsed.analyses}
    now = timezone.now()
    with transaction.atomic():
        for comment in comments:
            item = by_id[comment.id]
            comment.sentiment = item.sentiment
            comment.intent = item.intent
            comment.is_question = item.is_question
            comment.is_collaboration_opportunity = item.is_collaboration_opportunity
            comment.confidence = item.confidence
            comment.analysis_summary = item.summary
            comment.analyzed_at = now
            comment.save(
                update_fields=[
                    "sentiment",
                    "intent",
                    "is_question",
                    "is_collaboration_opportunity",
                    "confidence",
                    "analysis_summary",
                    "analyzed_at",
                    "updated_at",
                ]
            )
    return list(
        Comment.objects.filter(workspace=workspace, id__in=expected_ids)
        .select_related("post")
        .order_by("id")
    )


def get_workspace_comment(workspace, comment_id: int) -> Comment:
    return get_object_or_404(
        Comment.objects.select_related("post", "post__social_account").filter(
            workspace=workspace
        ),
        pk=comment_id,
    )


def suggest_comment_reply(*, workspace, user, comment: Comment, request_data: dict):
    brand_profile = build_brand_profile(user, workspace)
    tone = request_data.get("tone") or brand_profile["tone"]
    language = request_data.get("language") or brand_profile["preferred_language"]
    reply_request = {
        "tone": tone,
        "language": language,
        "extra_instructions": request_data.get("extra_instructions", ""),
    }

    parsed = generate_ai_structured(
        feature="comment_reply",
        workspace=workspace,
        user=user,
        prompt=build_reply_prompt(
            comment={
                "comment_id": comment.id,
                "author_username": comment.author_username,
                "text": comment.text[:2000],
                "sentiment": comment.sentiment,
                "intent": comment.intent,
                "is_question": comment.is_question,
                "is_collaboration_opportunity": comment.is_collaboration_opportunity,
            },
            post_context={
                "post_id": comment.post_id,
                "caption": (comment.post.caption or "")[:1000],
                "media_type": comment.post.media_type,
                "platform": comment.post.social_account.platform,
                "published_at": comment.post.published_at.isoformat(),
            },
            brand_profile=brand_profile,
            request_data=reply_request,
        ),
        response_schema=ReplySuggestionsResult,
        temperature=0.6,
    )

    suggestions = [item.model_dump() for item in parsed.suggestions]
    return CommentReplySuggestion.objects.create(
        workspace=workspace,
        comment=comment,
        created_by=user,
        suggestions=suggestions,
        tone=tone[:50],
        model_used=settings.GEMINI_MODEL,
    )
