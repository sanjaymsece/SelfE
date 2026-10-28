from django.conf import settings

from ai.prompts.reels import build_reel_prompt
from ai.schemas import ReelPlanResult
from ai.service import generate_ai_structured
from apps.analytics.selectors import build_performance_context
from apps.reel_generator.models import ReelPlan
from apps.workspaces.services import build_brand_profile


def generate_reel_plan(*, workspace, user, request_data: dict) -> ReelPlan:
    brand_profile = build_brand_profile(user, workspace)
    performance_context = build_performance_context(workspace, days=30)

    parsed = generate_ai_structured(
        feature="reel_plan",
        workspace=workspace,
        user=user,
        prompt=build_reel_prompt(
            request_data=request_data,
            brand_profile=brand_profile,
            performance_context=performance_context,
        ),
        response_schema=ReelPlanResult,
        temperature=0.7,
    )
    plan = parsed.model_dump()

    return ReelPlan.objects.create(
        workspace=workspace,
        created_by=user,
        title=plan["title"][:150],
        topic=request_data["topic"],
        platform=request_data["platform"],
        target_duration_seconds=request_data["duration_seconds"],
        plan=plan,
        model_used=settings.GEMINI_MODEL,
    )
