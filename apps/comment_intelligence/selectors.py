from django.db.models import Q

from apps.comment_intelligence.models import Comment


def comments_for_workspace(
    workspace,
    *,
    sentiment=None,
    intent=None,
    post_id=None,
    is_question=None,
    analyzed=None,
    search=None,
):
    queryset = Comment.objects.filter(workspace=workspace).select_related("post")
    if sentiment:
        queryset = queryset.filter(sentiment=sentiment)
    if intent:
        queryset = queryset.filter(intent=intent)
    if post_id is not None:
        queryset = queryset.filter(post_id=post_id)
    if is_question is not None:
        queryset = queryset.filter(is_question=is_question)
    if analyzed is True:
        queryset = queryset.filter(analyzed_at__isnull=False)
    elif analyzed is False:
        queryset = queryset.filter(analyzed_at__isnull=True)
    if search:
        queryset = queryset.filter(
            Q(text__icontains=search) | Q(author_username__icontains=search)
        )
    return queryset
