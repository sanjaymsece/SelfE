from django.urls import path

from apps.comment_intelligence.views import (
    AnalyzeCommentsView,
    CommentDetailView,
    CommentListView,
    SuggestReplyView,
)
from apps.comment_intelligence.webhook_views import InstagramWebhookView

app_name = "comment_intelligence"

urlpatterns = [
    path("webhook/", InstagramWebhookView.as_view(), name="instagram-webhook"),
    path("", CommentListView.as_view(), name="list"),
    path("<int:pk>/", CommentDetailView.as_view(), name="detail"),
    path("analyze/", AnalyzeCommentsView.as_view(), name="analyze"),
    path(
        "<int:pk>/suggest-reply/",
        SuggestReplyView.as_view(),
        name="suggest-reply",
    ),
]
