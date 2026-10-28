from django.urls import path

from apps.reel_generator.views import (
    GenerateReelView,
    ReelPlanDetailView,
    ReelPlanListCreateView,
)

app_name = "reel_generator"

urlpatterns = [
    path("generate/", GenerateReelView.as_view(), name="generate"),
    path("", ReelPlanListCreateView.as_view(), name="list"),
    path("<int:pk>/", ReelPlanDetailView.as_view(), name="detail"),
]
