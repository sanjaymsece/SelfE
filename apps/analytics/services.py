from django.conf import settings

from ai.prompts.analytics import build_analytics_explanation_prompt
from ai.schemas import AnalyticsExplanation
from ai.service import generate_ai_structured
from apps.analytics.models import AnalyticsReport
from apps.analytics.selectors import (
    METRIC_DEFINITIONS,
    DateRange,
    build_overview,
    insights_for_range,
    posting_time_recommendations,
)
from apps.common.exceptions import NoDataForPeriod


def generate_analytics_report(*, workspace, user, date_range: DateRange) -> AnalyticsReport:
    if not insights_for_range(workspace, date_range).exists():
        raise NoDataForPeriod()

    overview = build_overview(workspace, date_range, include_series=False)
    posting = posting_time_recommendations(
        workspace,
        date_range,
        min_sample=1,
        limit=5,
    )
    metrics = {
        "data_source": "simulated",
        "timezone": workspace.timezone,
        "period": overview["period"],
        "comparison_period": overview["comparison_period"],
        "totals": overview["totals"],
        "previous_totals": overview["previous_totals"],
        "growth": overview["growth"],
        "top_posts": overview["top_posts"][:5],
        "posting_recommendations": posting["recommendations"],
        "metric_definitions": METRIC_DEFINITIONS,
    }

    prompt_payload = {
        "data_source": "simulated",
        "period": metrics["period"],
        "comparison_period": metrics["comparison_period"],
        "current_totals": metrics["totals"],
        "previous_totals": metrics["previous_totals"],
        "growth": metrics["growth"],
        "top_posts": [
            {
                "caption": post["caption"][:200],
                "media_type": post["media_type"],
                "platform": post["platform"],
                "metrics": post["metrics"],
            }
            for post in metrics["top_posts"]
        ],
        "posting_recommendations": posting["recommendations"],
        "metric_formulas": METRIC_DEFINITIONS,
    }
    explanation = generate_ai_structured(
        feature="analytics_report",
        workspace=workspace,
        user=user,
        prompt=build_analytics_explanation_prompt(prompt_payload),
        response_schema=AnalyticsExplanation,
        temperature=0.2,
    )

    # Persisted only after validated AI output succeeds. Metrics are copied from
    # the deterministic calculations, never from the model.
    return AnalyticsReport.objects.create(
        workspace=workspace,
        created_by=user,
        date_from=date_range.date_from,
        date_to=date_range.date_to,
        metrics=metrics,
        explanation=explanation.model_dump(),
        model_used=settings.GEMINI_MODEL,
        data_source="simulated",
    )
