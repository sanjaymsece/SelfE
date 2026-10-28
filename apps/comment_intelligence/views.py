from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comment_intelligence.models import CommentIntent, CommentSentiment
from apps.comment_intelligence.selectors import comments_for_workspace
from apps.comment_intelligence.serializers import (
    CommentAnalysisRequestSerializer,
    CommentQuerySerializer,
    CommentReplySuggestionSerializer,
    CommentSerializer,
    CommentUpdateSerializer,
    ReplyRequestSerializer,
)
from apps.comment_intelligence.services import (
    analyze_comments,
    get_workspace_comment,
    suggest_comment_reply,
)
from apps.common.throttling import AIUserThrottle
from apps.workspaces.mixins import WORKSPACE_HEADER_PARAMETER, WorkspaceMixin


@extend_schema(
    tags=["comment intelligence"],
    summary="List simulated comments in the active workspace",
    parameters=[
        WORKSPACE_HEADER_PARAMETER,
        OpenApiParameter(
            name="sentiment",
            type=str,
            enum=CommentSentiment.values,
            required=False,
        ),
        OpenApiParameter(
            name="intent",
            type=str,
            enum=CommentIntent.values,
            required=False,
        ),
        OpenApiParameter(name="post", type=int, required=False),
        OpenApiParameter(name="is_question", type=bool, required=False),
        OpenApiParameter(name="analyzed", type=bool, required=False),
        OpenApiParameter(name="search", type=str, required=False),
    ],
    responses={200: CommentSerializer(many=True)},
)
class CommentListView(WorkspaceMixin, ListAPIView):
    serializer_class = CommentSerializer
    filter_backends = [SearchFilter]
    search_fields = ["text", "author_username"]

    def get_queryset(self):
        filters = CommentQuerySerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)
        return comments_for_workspace(
            self.get_workspace(),
            sentiment=filters.validated_data.get("sentiment"),
            intent=filters.validated_data.get("intent"),
            post_id=filters.validated_data.get("post"),
            is_question=filters.validated_data.get("is_question"),
            analyzed=filters.validated_data.get("analyzed"),
            search=filters.validated_data.get("search"),
        )


@extend_schema(
    tags=["comment intelligence"],
    summary="Classify comments with Gemini",
    description=(
        "Classifies up to 50 comments belonging to the authenticated workspace. "
        "If comment_ids is omitted, unanalyzed comments are selected. Every "
        "requested comment must be returned exactly once; otherwise no comment is "
        "updated and an AI validation error is returned."
    ),
    parameters=[WORKSPACE_HEADER_PARAMETER],
    request=CommentAnalysisRequestSerializer,
    responses={200: OpenApiResponse(description="Analyzed comments.")},
)
class AnalyzeCommentsView(WorkspaceMixin, APIView):
    throttle_classes = [AIUserThrottle]

    def post(self, request):
        serializer = CommentAnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comments = analyze_comments(
            workspace=self.get_workspace(),
            user=request.user,
            comment_ids=serializer.validated_data.get("comment_ids"),
        )
        return Response(
            {
                "analyzed": CommentSerializer(comments, many=True).data,
                "count": len(comments),
                "data_source": "simulated",
            }
        )


@extend_schema(
    tags=["comment intelligence"],
    summary="Generate contextual reply suggestions for a comment",
    description=(
        "Fetches the comment only from the authenticated workspace and saves the "
        "validated suggestions against that comment. No suggestion is saved on AI "
        "failure. Cross-tenant comment IDs return 404."
    ),
    parameters=[WORKSPACE_HEADER_PARAMETER],
    request=ReplyRequestSerializer,
    responses={201: CommentReplySuggestionSerializer},
)
class SuggestReplyView(WorkspaceMixin, APIView):
    throttle_classes = [AIUserThrottle]

    def post(self, request, pk):
        comment = get_workspace_comment(self.get_workspace(), pk)
        serializer = ReplyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        suggestion = suggest_comment_reply(
            workspace=self.get_workspace(),
            user=request.user,
            comment=comment,
            request_data=serializer.validated_data,
        )
        return Response(
            CommentReplySuggestionSerializer(suggestion).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["comment intelligence"],
    summary="Retrieve, update, or delete a comment in the active workspace",
    parameters=[WORKSPACE_HEADER_PARAMETER],
    responses={200: CommentSerializer, 204: None},
)
class CommentDetailView(WorkspaceMixin, RetrieveUpdateDestroyAPIView):
    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return CommentUpdateSerializer
        return CommentSerializer

    def get_queryset(self):
        return comments_for_workspace(self.get_workspace())
