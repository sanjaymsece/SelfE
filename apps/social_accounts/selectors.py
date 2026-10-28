from django.db.models import Count

from apps.social_accounts.models import SocialAccount


def social_accounts_for_workspace(workspace, platform=None):
    queryset = (
        SocialAccount.objects.filter(workspace=workspace)
        .annotate(posts_count=Count("posts"))
        .order_by("platform", "handle")
    )
    if platform:
        queryset = queryset.filter(platform=platform)
    return queryset
