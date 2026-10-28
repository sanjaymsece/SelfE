from django.conf import settings

from ai.prompts.content import build_content_prompt
from ai.schemas import CaptionsResult, ContentIdeasResult, ScriptsResult
from ai.service import generate_ai_structured
from apps.analytics.selectors import build_performance_context
from apps.content_studio.models import ContentDraft, DraftKind, DraftSource
from apps.workspaces.services import build_brand_profile

SCHEMAS = {
    "ideas": ContentIdeasResult,
    "captions": CaptionsResult,
    "scripts": ScriptsResult,
}
KIND_BY_TASK = {
    "ideas": DraftKind.IDEA,
    "captions": DraftKind.CAPTION,
    "scripts": DraftKind.SCRIPT,
}
TITLE_BY_TASK = {
    "ideas": "Content ideas",
    "captions": "Caption variants",
    "scripts": "Video script",
}


def _title_for(task: str, request_data: dict, brand_profile: dict) -> str:
    subject = (
        request_data.get("topic")
        or brand_profile.get("niche")
        or "Untitled"
    )
    return f"{TITLE_BY_TASK[task]}: {subject}"[:200]


def _body_for(task: str, content: dict) -> str:
    if task == "ideas":
        return "\n\n".join(
            f"{idea['title']}\n{idea['hook']}\n{idea['angle']}"
            for idea in content["ideas"]
        )
    if task == "captions":
        return "\n\n---\n\n".join(
            caption["text"] for caption in content["captions"]
        )
    return "\n\n---\n\n".join(
        f"{script['title']}\n{script['hook']}" for script in content["scripts"]
    )


def _prepare_request_data(task: str, request_data: dict, brand_profile: dict) -> dict:
    data = dict(request_data)
    data["task"] = task
    # Empty overrides fall back to saved preferences.
    if not data.get("tone"):
        data["tone"] = brand_profile.get("tone", "")
    if not data.get("language"):
        data["language"] = brand_profile.get("preferred_language", "")
    data["brand"] = {
        "niche": brand_profile.get("niche", ""),
        "goals": brand_profile.get("goals", []),
        "target_audience": brand_profile.get("target_audience", ""),
        "content_style": brand_profile.get("content_style", ""),
    }
    return data


def generate_content(*, task: str, workspace, user, request_data: dict):
    if task not in SCHEMAS:
        raise ValueError("Unsupported content generation task.")

    brand_profile = build_brand_profile(user, workspace)
    performance_context = build_performance_context(workspace, days=30)
    prepared = _prepare_request_data(task, request_data, brand_profile)
    schema = SCHEMAS[task]

    parsed = generate_ai_structured(
        feature=f"content_{task}",
        workspace=workspace,
        user=user,
        prompt=build_content_prompt(
            task=task,
            request_data=prepared,
            brand_profile=brand_profile,
            performance_context=performance_context,
        ),
        response_schema=schema,
        temperature=0.7,
    )
    content = parsed.model_dump()

    draft = ContentDraft.objects.create(
        workspace=workspace,
        created_by=user,
        kind=KIND_BY_TASK[task],
        title=_title_for(task, request_data, brand_profile),
        body=_body_for(task, content),
        content=content,
        source=DraftSource.AI,
        model_used=settings.GEMINI_MODEL,
        prompt_context={
            "data_source": "simulated",
            "analytics_window_days": 30,
            "request": request_data,
        },
    )
    return draft, content
