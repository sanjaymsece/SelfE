from django.urls import path

from apps.social_accounts.views import (
    InstagramLiveConnectView,
    SocialAccountDetailView,
    SocialAccountListView,
)

app_name = "social_accounts"

urlpatterns = [
    path("", SocialAccountListView.as_view(), name="list"),
    path("instagram-connect/", InstagramLiveConnectView.as_view(), name="instagram-connect"),
    path("<int:pk>/", SocialAccountDetailView.as_view(), name="detail"),
]
