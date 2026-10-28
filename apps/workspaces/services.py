from apps.accounts.models import UserPreference


def build_brand_profile(user, workspace) -> dict:
    """Tenant-scoped profile used by content, Reel, and reply prompts."""
    preference = getattr(user, "preferences", None)
    if preference is None:
        preference = UserPreference.objects.filter(user=user).first()
    return {
        "workspace": workspace.name,
        "workspace_timezone": workspace.timezone,
        "niche": (preference.niche if preference else "") or workspace.niche,
        "goals": preference.goals if preference else [],
        "preferred_language": preference.preferred_language if preference else "en",
        "tone": preference.tone if preference else "friendly",
        "content_style": preference.content_style if preference else "educational",
        "target_audience": preference.target_audience if preference else "",
        "keywords": preference.keywords if preference else [],
    }
