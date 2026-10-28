from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings
from drf_spectacular.utils import OpenApiParameter

from apps.common.exceptions import (
    InvalidWorkspace,
    NoWorkspace,
    WorkspaceAccessDenied,
    WorkspaceRequired,
)
from apps.workspaces.models import Workspace

WORKSPACE_HEADER_PARAMETER = OpenApiParameter(
    name="X-Workspace-ID",
    type=int,
    location=OpenApiParameter.HEADER,
    required=False,
    description=(
        "Workspace to act in. Required only when the authenticated user belongs "
        "to more than one workspace. Membership is verified server-side."
    ),
)


class WorkspaceMixin:
    """Resolve and authorize the active workspace for a request.

    The client-supplied header is never treated as proof of access: the resolved
    workspace must be in the authenticated user's membership queryset.
    """

    permission_classes = [IsAuthenticated]

    def get_workspace(self) -> Workspace:
        cached = getattr(self, "_workspace", None)
        if cached is not None:
            return cached

        request = self.request
        user = request.user
        if not user or not user.is_authenticated:
            raise WorkspaceAccessDenied()

        memberships = Workspace.objects.for_user(user)
        raw_header = request.headers.get("X-Workspace-ID")

        if raw_header not in (None, ""):
            try:
                workspace_id = int(raw_header)
            except (TypeError, ValueError) as exc:
                raise InvalidWorkspace() from exc
            workspace = memberships.filter(pk=workspace_id).first()
            if workspace is None:
                raise WorkspaceAccessDenied()
        else:
            count = memberships.count()
            if count == 0:
                raise NoWorkspace()
            if count > 1:
                raise WorkspaceRequired()
            workspace = memberships.first()

        self._workspace = workspace
        return workspace


def get_workspace_or_404(workspace_queryset, workspace: Workspace):
    """Convenience for object lookups inside an already-authorized workspace."""
    return get_object_or_404(workspace_queryset, workspace=workspace)
