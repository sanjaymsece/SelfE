from dataclasses import dataclass
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Count, Sum
from django.utils import timezone

from apps.analytics.models import PostInsight
from apps.common.exceptions import InvalidDateRange
from apps.social_accounts.models import Post

METRIC_DEFINITIONS = {
    "views": "Sum of daily simulated views for posts in the period.",
    "reach": (
        "Sum of daily simulated post reach. This is not unique audience reach; "
        "the same account may be counted across posts and days."
    ),
    "engagement": "likes + comments + shares + saves.",
    "engagement_rate": (
        "engagement / reach * 100. Returns 0 when reach is 0."
    ),
    "reach_rate": "reach / views * 100. Returns 0 when views is 0.",
    "save_rate": "saves / reach * 100. Returns 0 when reach is 0.",
    "growth": (
        "(current - previous) / previous * 100. Null when the comparison "
        "period has no data for that metric."
    ),
    "posting_time_score": (
        "Mean of each post's engagement rate, grouped by the post's publication "
        "weekday and hour in the workspace timezone. Each post contributes once."
    ),
}


@dataclass(frozen=True)
class DateRange:
    date_from: date
    date_to: date

    @property
    def days(self) -> int:
        return (self.date_to - self.date_from).days + 1

    def previous(self) -> "DateRange":
        previous_to = self.date_from - timedelta(days=1)
        previous_from = previous_to - timedelta(days=self.days - 1)
        return DateRange(previous_from, previous_to)

    def as_dict(self) -> dict:
        return {
            "date_from": self.date_from.isoformat(),
            "date_to": self.date_to.isoformat(),
            "days": self.days,
        }


def resolve_date_range(
    date_from: date | None = None,
    date_to: date | None = None,
) -> DateRange:
    date_to = date_to or timezone.localdate()
    date_from = date_from or (
        date_to - timedelta(days=settings.ANALYTICS_DEFAULT_DAYS - 1)
    )
    if date_from > date_to:
        raise InvalidDateRange("date_from must be on or before date_to.")
    days = (date_to - date_from).days + 1
    if days > settings.ANALYTICS_MAX_RANGE_DAYS:
        raise InvalidDateRange(
            f"Date ranges may not exceed {settings.ANALYTICS_MAX_RANGE_DAYS} days."
        )
    return DateRange(date_from, date_to)


def insights_for_range(workspace, date_range: DateRange):
    return PostInsight.objects.filter(
        workspace=workspace,
        date__range=(date_range.date_from, date_range.date_to),
    )


def _sum_metrics(queryset) -> dict:
    totals = queryset.aggregate(
        views=Sum("views"),
        reach=Sum("reach"),
        likes=Sum("likes"),
        comments=Sum("comments"),
        shares=Sum("shares"),
        saves=Sum("saves"),
    )
    views = int(totals["views"] or 0)
    reach = int(totals["reach"] or 0)
    likes = int(totals["likes"] or 0)
    comments = int(totals["comments"] or 0)
    shares = int(totals["shares"] or 0)
    saves = int(totals["saves"] or 0)
    engagement = likes + comments + shares + saves
    return {
        "views": views,
        "reach": reach,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "saves": saves,
        "engagement": engagement,
        "engagement_rate": round(engagement / reach * 100, 2) if reach else 0.0,
        "reach_rate": round(reach / views * 100, 2) if views else 0.0,
        "save_rate": round(saves / reach * 100, 2) if reach else 0.0,
    }


def summarize_totals(queryset) -> dict:
    data = _sum_metrics(queryset)
    data["posts"] = queryset.values("post_id").distinct().count()
    return data


def _growth(current: int | float, previous: int | float):
    if not previous:
        return None
    return round((current - previous) / previous * 100, 2)


def build_growth(current: dict, previous: dict) -> dict:
    keys = ["views", "reach", "likes", "comments", "shares", "saves", "engagement", "posts"]
    growth = {f"{key}_pct": _growth(current.get(key, 0), previous.get(key, 0)) for key in keys}
    growth["engagement_rate_change_points"] = round(
        current.get("engagement_rate", 0.0) - previous.get("engagement_rate", 0.0),
        2,
    )
    growth["has_prior_data"] = bool(previous.get("views") or previous.get("reach"))
    return growth


def build_daily_series(queryset) -> list[dict]:
    rows = (
        queryset.values("date")
        .annotate(
            views=Sum("views"),
            reach=Sum("reach"),
            likes=Sum("likes"),
            comments=Sum("comments"),
            shares=Sum("shares"),
            saves=Sum("saves"),
            posts=Count("post_id", distinct=True),
        )
        .order_by("date")
    )
    series = []
    for row in rows:
        engagement = (
            int(row["likes"] or 0)
            + int(row["comments"] or 0)
            + int(row["shares"] or 0)
            + int(row["saves"] or 0)
        )
        reach = int(row["reach"] or 0)
        series.append(
            {
                "date": row["date"].isoformat(),
                "views": int(row["views"] or 0),
                "reach": reach,
                "engagement": engagement,
                "engagement_rate": round(engagement / reach * 100, 2) if reach else 0.0,
                "posts": row["posts"],
            }
        )
    return series


def _post_aggregates(queryset) -> dict[int, dict]:
    rows = (
        queryset.values("post_id")
        .annotate(
            views=Sum("views"),
            reach=Sum("reach"),
            likes=Sum("likes"),
            comments=Sum("comments"),
            shares=Sum("shares"),
            saves=Sum("saves"),
        )
        .order_by("post_id")
    )
    result = {}
    for row in rows:
        reach = int(row["reach"] or 0)
        likes = int(row["likes"] or 0)
        comments = int(row["comments"] or 0)
        shares = int(row["shares"] or 0)
        saves = int(row["saves"] or 0)
        engagement = likes + comments + shares + saves
        result[row["post_id"]] = {
            "views": int(row["views"] or 0),
            "reach": reach,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saves,
            "engagement": engagement,
            "engagement_rate": round(engagement / reach * 100, 2) if reach else 0.0,
            "reach_rate": round(reach / int(row["views"]), 2) if row["views"] else 0.0,
            "save_rate": round(saves / reach * 100, 2) if reach else 0.0,
        }
    return result


def post_metrics_for_range(
    workspace,
    date_range: DateRange,
    *,
    platform: str | None = None,
    media_type: str | None = None,
) -> list[dict]:
    insight_qs = insights_for_range(workspace, date_range)
    post_filter = {}
    if platform:
        post_filter["social_account__platform"] = platform
    if media_type:
        post_filter["media_type"] = media_type
    if post_filter:
        insight_qs = insight_qs.filter(
            post__in=Post.objects.filter(workspace=workspace, **post_filter)
        )

    aggregates = _post_aggregates(insight_qs)
    posts = {
        post.id: post
        for post in Post.objects.filter(id__in=aggregates.keys()).select_related(
            "social_account"
        )
    }
    result = []
    for post_id, metrics in aggregates.items():
        post = posts.get(post_id)
        if post is None:
            continue
        result.append(
            {
                "id": post.id,
                "external_id": post.external_id,
                "caption": post.caption,
                "media_type": post.media_type,
                "platform": post.social_account.platform,
                "social_account": {
                    "id": post.social_account_id,
                    "handle": post.social_account.handle,
                    "platform": post.social_account.platform,
                },
                "permalink": post.permalink,
                "published_at": post.published_at.isoformat(),
                "is_simulated": post.is_simulated,
                "metrics": metrics,
            }
        )

    result.sort(
        key=lambda item: (
            item["metrics"]["engagement_rate"],
            item["metrics"]["engagement"],
            item["id"],
        ),
        reverse=True,
    )
    return result


def build_overview(workspace, date_range: DateRange, *, include_series: bool = True) -> dict:
    queryset = insights_for_range(workspace, date_range)
    totals = summarize_totals(queryset)
    previous_range = date_range.previous()
    previous_totals = summarize_totals(insights_for_range(workspace, previous_range))
    top_posts = post_metrics_for_range(workspace, date_range)[:5]

    overview = {
        "data_source": "simulated",
        "timezone": workspace.timezone,
        "period": date_range.as_dict(),
        "comparison_period": previous_range.as_dict(),
        "totals": totals,
        "previous_totals": previous_totals,
        "growth": build_growth(totals, previous_totals),
        "has_data": totals["views"] > 0 or totals["reach"] > 0,
        "top_posts": top_posts,
        "metric_definitions": METRIC_DEFINITIONS,
    }
    if include_series:
        overview["daily_series"] = build_daily_series(queryset)
    return overview


def _confidence(sample_size: int) -> str:
    if sample_size >= 6:
        return "high"
    if sample_size >= 3:
        return "medium"
    return "low"


def posting_time_recommendations(
    workspace,
    date_range: DateRange,
    *,
    platform: str | None = None,
    min_sample: int | None = None,
    limit: int | None = None,
) -> dict:
    min_sample = min_sample or settings.POSTING_TIME_MIN_SAMPLE
    limit = limit or settings.POSTING_TIME_MAX_RECOMMENDATIONS

    posts = Post.objects.filter(
        workspace=workspace,
        insights__date__range=(date_range.date_from, date_range.date_to),
    ).select_related("social_account")
    if platform:
        posts = posts.filter(social_account__platform=platform)
    posts = posts.distinct()

    insight_qs = insights_for_range(workspace, date_range)
    if platform:
        insight_qs = insight_qs.filter(post__social_account__platform=platform)
    aggregates = _post_aggregates(insight_qs)

    tz = ZoneInfo(workspace.timezone)
    slots: dict[tuple[int, int], dict] = {}
    counted_posts = 0
    for post in posts:
        metrics = aggregates.get(post.id)
        if not metrics or not metrics["reach"]:
            continue
        local_published = post.published_at.astimezone(tz)
        key = (local_published.weekday(), local_published.hour)
        slot = slots.setdefault(
            key,
            {
                "day_of_week": key[0],
                "hour": key[1],
                "sample_size": 0,
                "_rate_sum": 0.0,
                "total_engagement": 0,
                "total_reach": 0,
                "total_views": 0,
            },
        )
        slot["sample_size"] += 1
        slot["_rate_sum"] += metrics["engagement_rate"]
        slot["total_engagement"] += metrics["engagement"]
        slot["total_reach"] += metrics["reach"]
        slot["total_views"] += metrics["views"]
        counted_posts += 1

    all_slots = []
    for slot in slots.values():
        avg_rate = round(slot["_rate_sum"] / slot["sample_size"], 2)
        all_slots.append(
            {
                "day_of_week": slot["day_of_week"],
                "day_label": [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ][slot["day_of_week"]],
                "hour": slot["hour"],
                "hour_label": f"{slot['hour']:02d}:00",
                "sample_size": slot["sample_size"],
                "avg_engagement_rate": avg_rate,
                "average_engagement_per_post": round(
                    slot["total_engagement"] / slot["sample_size"], 2
                ),
                "total_engagement": slot["total_engagement"],
                "total_reach": slot["total_reach"],
                "confidence": _confidence(slot["sample_size"]),
            }
        )

    all_slots.sort(
        key=lambda item: (
            item["avg_engagement_rate"],
            item["total_engagement"],
            item["sample_size"],
        ),
        reverse=True,
    )
    qualified = [slot for slot in all_slots if slot["sample_size"] >= min_sample]
    note = None
    if not qualified and all_slots:
        qualified = all_slots
        note = (
            "No posting slot met the requested minimum sample size; these are "
            "low-sample suggestions based on the available simulated posts."
        )
    recommendations = qualified[:limit]

    return {
        "data_source": "simulated",
        "timezone": workspace.timezone,
        "period": date_range.as_dict(),
        "sample_posts": counted_posts,
        "min_sample_size": min_sample,
        "methodology": {
            "grouping": "publication weekday and hour in the workspace timezone",
            "score": METRIC_DEFINITIONS["posting_time_score"],
            "caveat": (
                "Based only on simulated historical post performance. Correlation "
                "does not guarantee future results."
            ),
        },
        "recommendations": recommendations,
        "all_slots": all_slots,
        "note": note,
    }


def build_performance_context(workspace, days: int = 30) -> dict:
    """Compact, tenant-scoped analytics context for content and Reel prompts."""
    date_to = timezone.localdate()
    date_from = date_to - timedelta(days=days - 1)
    date_range = DateRange(date_from, date_to)
    overview = build_overview(workspace, date_range, include_series=False)
    posting = posting_time_recommendations(
        workspace,
        date_range,
        min_sample=1,
        limit=3,
    )
    from apps.analytics.models import AnalyticsReport

    latest_report = AnalyticsReport.objects.filter(workspace=workspace).first()
    findings = []
    if latest_report:
        findings = latest_report.explanation.get("key_findings", [])[:5]

    return {
        "data_source": "simulated",
        "window_days": days,
        "totals": overview["totals"],
        "growth": overview["growth"],
        "top_posts": [
            {
                "caption": (post["caption"] or "")[:240],
                "media_type": post["media_type"],
                "platform": post["platform"],
                "engagement_rate": post["metrics"]["engagement_rate"],
                "views": post["metrics"]["views"],
                "saves": post["metrics"]["saves"],
            }
            for post in overview["top_posts"][:3]
        ],
        "best_posting_slots": [
            {
                "day": slot["day_label"],
                "hour": slot["hour_label"],
                "avg_engagement_rate": slot["avg_engagement_rate"],
                "sample_size": slot["sample_size"],
            }
            for slot in posting["recommendations"][:3]
        ],
        "latest_analytics_findings": findings,
    }
