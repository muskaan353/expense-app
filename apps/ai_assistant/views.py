from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_assistant.serializers import (
    AssistantQuerySerializer,
    AssistantResponseSerializer,
)
from apps.ai_assistant.services import answer_balance_question
from apps.groups.selectors import accessible_groups_for


class AssistantQueryView(APIView):
    @extend_schema(
        request=AssistantQuerySerializer,
        responses=AssistantResponseSerializer,
    )
    def post(self, request):
        serializer = AssistantQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.validated_data["group"]
        if not accessible_groups_for(user=request.user).filter(pk=group.pk).exists():
            raise PermissionDenied("You do not have access to this group.")
        result = answer_balance_question(
            group=group,
            user=request.user,
            question=serializer.validated_data["question"],
        )
        return Response(AssistantResponseSerializer(result).data)
