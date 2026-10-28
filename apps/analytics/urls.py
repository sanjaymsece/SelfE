from django.urls import path

from apps.analytics.views import (
    AnalyticsOverviewView,
    AnalyticsPostsView,
    AnalyticsReportDetailView,
    AnalyticsReportListView,
    GenerateAnalyticsReportView,
    PostingTimesView,
)

app_name = "analytics"

urlpatterns = [
    path("overview/", AnalyticsOverviewView.as_view(), name="overview"),
    path("posts/", AnalyticsPostsView.as_view(), name="posts"),
    path("reports/", AnalyticsReportListView.as_view(), name="reports"),
    path("reports/generate/", GenerateAnalyticsReportView.as_view(), name="report-generate"),
    path("reports/<int:pk>/", AnalyticsReportDetailView.as_view(), name="report-detail"),
    path("posting-times/", PostingTimesView.as_view(), name="posting-times"),
]
