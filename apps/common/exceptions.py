from rest_framework.exceptions import APIException


class WorkspaceRequired(APIException):
    status_code = 400
    default_detail = (
        "A workspace must be selected with the X-Workspace-ID header because "
        "your account belongs to more than one workspace."
    )
    default_code = "workspace_required"


class WorkspaceAccessDenied(APIException):
    status_code = 403
    default_detail = "You do not have access to the requested workspace."
    default_code = "workspace_forbidden"


class InvalidWorkspace(APIException):
    status_code = 400
    default_detail = "X-Workspace-ID must be a valid workspace identifier."
    default_code = "invalid_workspace"


class NoWorkspace(APIException):
    status_code = 403
    default_detail = "Your account does not belong to a workspace."
    default_code = "no_workspace"


class NoDataForPeriod(APIException):
    status_code = 400
    default_detail = "There is no simulated analytics data for the requested period."
    default_code = "no_data_for_period"


class InvalidDateRange(APIException):
    status_code = 400
    default_detail = "The requested date range is invalid."
    default_code = "invalid_date_range"


class NoCommentsToAnalyze(APIException):
    status_code = 400
    default_detail = (
        "There are no unanalyzed comments to process. Provide comment_ids or "
        "wait for new comments."
    )
    default_code = "no_comments_to_analyze"
