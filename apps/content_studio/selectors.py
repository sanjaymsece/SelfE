from django.db.models import Q

from apps.content_studio.models import ContentDraft


def drafts_for_workspace(workspace, *, kind=None, status=None, search=None):
    queryset = ContentDraft.objects.filter(workspace=workspace).select_related(
        "created_by"
    )
    if kind:
        queryset = queryset.filter(kind=kind)
    if status:
        queryset = queryset.filter(status=status)
    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(body__icontains=search))
    return queryset
