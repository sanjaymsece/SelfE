import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, HttpResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from config.error_views import api_404, api_500


def serve_frontend_spa(request):
    dist_index = settings.BASE_DIR / "frontend" / "dist" / "index.html"
    if os.path.exists(dist_index):
        return FileResponse(open(dist_index, "rb"))
    return HttpResponse(
        "SelfE API Server is running. Visit /api/v1/docs/ for Swagger UI, or run `npm run dev` in frontend/",
        content_type="text/plain",
    )


def serve_dist_file(request, filename):
    dist_file = settings.BASE_DIR / "frontend" / "dist" / filename
    if os.path.exists(dist_file) and os.path.isfile(dist_file):
        return FileResponse(open(dist_file, "rb"))
    return HttpResponse("File not found", status=404)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("unnamed.jpg", lambda r: serve_dist_file(r, "unnamed.jpg")),
    path("favicon.svg", lambda r: serve_dist_file(r, "favicon.svg")),
    path("icons.svg", lambda r: serve_dist_file(r, "icons.svg")),
    path("api/v1/", include("apps.common.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/workspaces/", include("apps.workspaces.urls")),
    path("api/v1/social-accounts/", include("apps.social_accounts.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/content/", include("apps.content_studio.urls")),
    path("api/v1/reels/", include("apps.reel_generator.urls")),
    path("api/v1/comments/", include("apps.comment_intelligence.urls")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/v1/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("", serve_frontend_spa, name="spa-index"),
]

dist_assets = settings.BASE_DIR / "frontend" / "dist" / "assets"
if os.path.exists(dist_assets):
    urlpatterns += static("/assets/", document_root=dist_assets)

handler404 = api_404
handler500 = api_500
