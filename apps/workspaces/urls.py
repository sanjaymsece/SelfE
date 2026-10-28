from django.urls import path

from apps.workspaces.views import WorkspaceDetailView, WorkspaceListCreateView

app_name = "workspaces"

urlpatterns = [
    path("", WorkspaceListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", WorkspaceDetailView.as_view(), name="detail"),
]
