from django.urls import path

from apps.content_studio.views import (
    AIChatCoPilotView,
    ContentDraftDetailView,
    ContentDraftListCreateView,
    GeminiTestView,
    GenerateCaptionsView,
    GenerateContentIdeasView,
    GenerateScriptsView,
    VoiceSynthesisView,
)

app_name = "content_studio"

urlpatterns = [
    path("chat/", AIChatCoPilotView.as_view(), name="copilot-chat"),
    path("voice/synthesize/", VoiceSynthesisView.as_view(), name="voice-synthesize"),
    path("gemini-test/", GeminiTestView.as_view(), name="gemini-test"),
    path("ideas/generate/", GenerateContentIdeasView.as_view(), name="ideas-generate"),
    path("captions/generate/", GenerateCaptionsView.as_view(), name="captions-generate"),
    path("scripts/generate/", GenerateScriptsView.as_view(), name="scripts-generate"),
    path("drafts/", ContentDraftListCreateView.as_view(), name="drafts"),
    path("drafts/<int:pk>/", ContentDraftDetailView.as_view(), name="draft-detail"),
]
