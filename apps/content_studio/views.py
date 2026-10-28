import logging
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status

logger = logging.getLogger(__name__)
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.throttling import AIUserThrottle
from apps.content_studio.models import DraftSource
from apps.content_studio.selectors import drafts_for_workspace
from apps.content_studio.serializers import (
    CaptionsRequestSerializer,
    ContentDraftQuerySerializer,
    ContentDraftSerializer,
    ContentIdeasRequestSerializer,
    ScriptsRequestSerializer,
)
from apps.content_studio.services import generate_content
from apps.workspaces.mixins import WORKSPACE_HEADER_PARAMETER, WorkspaceMixin


@extend_schema(
    tags=["content studio"],
    summary="List or create workspace content drafts",
    parameters=[WORKSPACE_HEADER_PARAMETER],
    request=ContentDraftSerializer,
    responses={200: ContentDraftSerializer(many=True), 201: ContentDraftSerializer},
)
class ContentDraftListCreateView(WorkspaceMixin, ListCreateAPIView):
    serializer_class = ContentDraftSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "body"]
    ordering_fields = ["created_at", "updated_at", "title"]
    ordering = ["-created_at", "-id"]

    def get_queryset(self):
        data = ContentDraftQuerySerializer(data=self.request.query_params)
        data.is_valid(raise_exception=True)
        return drafts_for_workspace(
            self.get_workspace(),
            kind=data.validated_data.get("kind"),
            status=data.validated_data.get("status"),
            search=data.validated_data.get("search"),
        )

    def perform_create(self, serializer):
        serializer.save(
            workspace=self.get_workspace(),
            created_by=self.request.user,
            source=DraftSource.MANUAL,
        )


@extend_schema(
    tags=["content studio"],
    summary="Retrieve, update, or delete a content draft",
    parameters=[WORKSPACE_HEADER_PARAMETER],
    request=ContentDraftSerializer,
    responses={200: ContentDraftSerializer, 204: OpenApiResponse(description="Deleted.")},
)
class ContentDraftDetailView(WorkspaceMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = ContentDraftSerializer

    def get_queryset(self):
        return drafts_for_workspace(self.get_workspace())


class GenerateContentView(WorkspaceMixin, APIView):
    generation_task = ""
    request_serializer_class = None
    result_key = ""
    throttle_classes = [AIUserThrottle]

    def post(self, request):
        serializer = self.request_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        workspace = self.get_workspace()
        draft, content = generate_content(
            task=self.generation_task,
            workspace=workspace,
            user=request.user,
            request_data=serializer.validated_data,
        )
        return Response(
            {
                "draft": ContentDraftSerializer(draft).data,
                self.result_key: content[self.result_key],
                "data_source": "simulated",
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["content studio"],
    summary="Test any custom Gemini API key or prompt",
    request=inline_serializer(
        name="GeminiTestRequest",
        fields={
            "api_key": serializers.CharField(required=False, default=""),
            "prompt": serializers.CharField(required=False, default=""),
            "save_to_env": serializers.BooleanField(required=False, default=False),
        },
    ),
    responses={200: inline_serializer(
        name="GeminiTestResponse",
        fields={
            "status": serializers.CharField(),
            "reply": serializers.CharField(),
            "strategy": serializers.CharField(),
            "model": serializers.CharField(),
            "latency_seconds": serializers.FloatField(),
            "api_key_valid": serializers.BooleanField(),
        },
    )},
)
class GeminiTestView(APIView):
    """
    Test any custom Gemini API key or prompt directly from the UI or API.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        import os
        from django.conf import settings
        api_key = request.data.get("api_key", "").strip() or settings.GEMINI_API_KEY.strip()
        prompt = request.data.get("prompt", "Generate an Instagram Reel hook for aesthetic lifestyle").strip()
        save_to_env = request.data.get("save_to_env", False)

        from pydantic import BaseModel
        class DynamicReply(BaseModel):
            reply: str
            why_it_works: str

        try:
            from ai.client import GeminiAIClient
            import time
            start = time.time()
            if api_key and api_key != settings.GEMINI_API_KEY:
                settings.GEMINI_API_KEY = api_key

            client = GeminiAIClient()
            res = client.generate_structured(
                prompt=f"Act as SocioSync AI Instagram Manager. Answer this creator prompt: {prompt}",
                response_schema=DynamicReply,
            )
            elapsed = round(time.time() - start, 2)

            if save_to_env and api_key:
                env_path = settings.BASE_DIR / ".env"
                if os.path.exists(env_path):
                    with open(env_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    with open(env_path, "w", encoding="utf-8") as f:
                        for l in lines:
                            if l.startswith("GEMINI_API_KEY="):
                                f.write(f"GEMINI_API_KEY={api_key}\n")
                            else:
                                f.write(l)

            return Response({
                "status": "ok",
                "reply": res.data.get("reply"),
                "strategy": res.data.get("why_it_works"),
                "model": res.model,
                "latency_seconds": elapsed,
                "api_key_valid": True,
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            cause = getattr(exc, "__cause__", None)
            cause_str = str(cause or "")
            if "API_KEY_INVALID" in cause_str or "API key not valid" in cause_str:
                error_msg = "Google Gemini rejected the API key: API key is invalid. Please create and copy a fresh key starting with 'AIzaSy...' from https://aistudio.google.com/apikey"
            elif "PERMISSION_DENIED" in cause_str:
                error_msg = "Google Gemini permission denied: API key lacks Generative Language API access."
            elif cause and getattr(cause, "message", None):
                error_msg = cause.message
            else:
                error_msg = str(cause or exc)

            return Response({
                "status": "error",
                "error": error_msg,
                "api_key_valid": False,
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["content studio"],
    summary="Interactive AI Co-Pilot chat endpoint",
    request=inline_serializer(
        name="AIChatRequest",
        fields={
            "prompt": serializers.CharField(required=True),
            "api_key": serializers.CharField(required=False, default=""),
        },
    ),
    responses={200: inline_serializer(
        name="AIChatResponse",
        fields={
            "status": serializers.CharField(),
            "reply": serializers.CharField(),
            "hook": serializers.CharField(),
            "why_it_works": serializers.CharField(),
            "model": serializers.CharField(),
        },
    )},
)
class AIChatCoPilotView(APIView):
    """
    Direct Gemini Co-Pilot Chat endpoint for main chat dialog, voice assistant, and orb prompts.
    Always uses the active Gemini API key from settings/.env or user-provided override.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from django.conf import settings
        prompt = request.data.get("prompt", "").strip()
        custom_key = request.data.get("api_key", "").strip()
        active_key = custom_key or getattr(settings, "GEMINI_API_KEY", "").strip()

        if not prompt:
            prompt = "Give me one fresh viral hook for an aesthetic Instagram Reel today."

        from pydantic import BaseModel, Field

        class CoPilotResponse(BaseModel):
            reply: str = Field(description="Direct, conversational, natural answer to the creator as their zero-salary AI manager.")
            hook: str = Field(description="A punchy 3-second hook for Instagram Reels if applicable, otherwise brief summary.", default="")
            why_it_works: str = Field(description="Algorithmic rationale or psychological reason for the suggestion.", default="")

        try:
            from ai.client import GeminiAIClient
            client = GeminiAIClient(api_key=active_key)
            system_context = (
                "You are SocioSync, an elite autonomous AI Instagram Manager working on zero salary for creator Sophia Tompson (@sophia.studio, 128.4K followers, lifestyle/aesthetic niche). "
                "Be direct, energetic, professional, highly creative, and strategic. "
                "Never repeat the same canned responses. Tailor your answer specifically to what the creator asks. "
                f"Creator Query: {prompt}"
            )
            res = client.generate_structured(
                prompt=system_context,
                response_schema=CoPilotResponse,
            )
            return Response({
                "status": "ok",
                "reply": res.data.get("reply"),
                "hook": res.data.get("hook"),
                "why_it_works": res.data.get("why_it_works"),
                "model": res.model,
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.warning(f"Co-pilot generation error: {exc}")
            cause = getattr(exc, "__cause__", None)
            err_msg = str(cause or exc)
            return Response({
                "status": "error",
                "error": err_msg,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=["content studio"],
    summary="Voice Synthesis endpoint (ElevenLabs & Neural Female Voice)",
    request=inline_serializer(
        name="VoiceSynthesisRequest",
        fields={
            "text": serializers.CharField(required=True),
            "voice_id": serializers.CharField(required=False, default="21m00Tcm4TlvDq8ikWAM"),
            "elevenlabs_api_key": serializers.CharField(required=False, default=""),
        },
    ),
    responses={200: OpenApiResponse(description="Audio MP3 stream")},
)
class VoiceSynthesisView(APIView):
    """
    Synthesizes natural, human-like voice audio (MP3).
    Supports ElevenLabs female voices (default: Rachel '21m00Tcm4TlvDq8ikWAM')
    with seamless fallback to Jenny Neural (high-fidelity Microsoft neural female voice).
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        import asyncio
        import os
        import re
        from django.conf import settings
        from django.http import HttpResponse
        import httpx

        text = request.data.get("text", "").strip()
        if not text:
            return Response({"error": "Text is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Clean text of markdown formatting and emojis for clean speech
        clean_text = re.sub(r'[*_#`"“”…—]', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        if len(clean_text) > 800:
            clean_text = clean_text[:800]

        elevenlabs_key = (
            request.data.get("elevenlabs_api_key", "").strip()
            or getattr(settings, "ELEVENLABS_API_KEY", "").strip()
            or os.getenv("ELEVENLABS_API_KEY", "").strip()
        )
        voice_id = request.data.get("voice_id", "").strip() or "21m00Tcm4TlvDq8ikWAM"  # Rachel (calm female)

        # 1. If ElevenLabs API Key is present, synthesize with ElevenLabs
        if elevenlabs_key:
            try:
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "xi-api-key": elevenlabs_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                }
                payload = {
                    "text": clean_text,
                    "model_id": "eleven_turbo_v2_5",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                    },
                }
                with httpx.Client(timeout=12.0) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200 and len(resp.content) > 500:
                        return HttpResponse(resp.content, content_type="audio/mpeg")
                    else:
                        logger.warning(
                            "ElevenLabs returned status %s: %s", resp.status_code, resp.text
                        )
            except Exception as e:
                logger.warning("ElevenLabs request failed, using neural voice: %s", e)

        # 2. High-fidelity Neural Female Voice via edge-tts (Jenny Neural - calm, natural, zero token cost)
        try:
            import edge_tts

            async def _generate_neural():
                communicate = edge_tts.Communicate(clean_text, "en-US-JennyNeural")
                chunks = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        chunks.append(chunk["data"])
                return b"".join(chunks)

            audio_data = asyncio.run(_generate_neural())
            if audio_data:
                response = HttpResponse(audio_data, content_type="audio/mpeg")
                response["Content-Length"] = str(len(audio_data))
                response["X-Voice-Engine"] = "Neural-Jenny-Female"
                return response
        except Exception as e:
            logger.error("Neural speech synthesis error: %s", e)

        return Response({"error": "Voice synthesis failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _generation_schema(task, serializer_class, result_key, description):
    def decorator(view_class):
        extend_schema(
            tags=["content studio"],
            summary=description,
            description=(
                "Uses the authenticated workspace's saved preferences and a "
                "compact summary of its simulated analytics. Gemini output is "
                "schema-validated; a failed AI call saves nothing and returns a "
                "structured error."
            ),
            parameters=[WORKSPACE_HEADER_PARAMETER],
            request=serializer_class,
            responses={
                201: OpenApiResponse(
                    description=f"Saved draft plus generated {result_key}."
                )
            },
        )(view_class)
        return view_class

    return decorator


@_generation_schema(
    "ideas",
    ContentIdeasRequestSerializer,
    "ideas",
    "Generate content ideas",
)
class GenerateContentIdeasView(GenerateContentView):
    generation_task = "ideas"
    request_serializer_class = ContentIdeasRequestSerializer
    result_key = "ideas"


@_generation_schema(
    "captions",
    CaptionsRequestSerializer,
    "captions",
    "Generate caption variants and hashtags",
)
class GenerateCaptionsView(GenerateContentView):
    generation_task = "captions"
    request_serializer_class = CaptionsRequestSerializer
    result_key = "captions"


@_generation_schema(
    "scripts",
    ScriptsRequestSerializer,
    "scripts",
    "Generate short-form video scripts",
)
class GenerateScriptsView(GenerateContentView):
    generation_task = "scripts"
    request_serializer_class = ScriptsRequestSerializer
    result_key = "scripts"
