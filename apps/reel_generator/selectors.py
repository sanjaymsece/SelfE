from django.db.models import Q

from apps.reel_generator.models import ReelPlan


def reels_for_workspace(workspace, *, status=None, platform=None, search=None):
    queryset = ReelPlan.objects.filter(workspace=workspace)
    if status:
        queryset = queryset.filter(status=status)
    if platform:
        queryset = queryset.filter(platform=platform)
    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(topic__icontains=search))
    return queryset
