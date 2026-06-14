from django.db.models import Q
from django.utils import timezone
from rest_framework import decorators, mixins, parsers, response, status, viewsets
from rest_framework.exceptions import PermissionDenied

from apps.imports.models import ImportIssue, ImportSession
from apps.imports.serializers import (
    ImportIssueSerializer,
    ImportRowSerializer,
    ImportSessionCreateSerializer,
    ImportSessionSerializer,
)
from apps.imports.services import stage_import


class ImportSessionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ImportSession.objects.select_related("group", "uploaded_by")
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)

    def get_queryset(self):
        now = timezone.now()
        return self.queryset.filter(
            Q(group__owner=self.request.user)
            | Q(
                group__memberships__user=self.request.user,
                group__memberships__joined_at__lte=now,
            )
            & (
                Q(group__memberships__left_at__isnull=True)
                | Q(group__memberships__left_at__gt=now)
            )
        ).distinct()

    def get_serializer_class(self):
        return (
            ImportSessionCreateSerializer
            if self.action == "create"
            else ImportSessionSerializer
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.validated_data["group"]
        if group.owner_id != request.user.id:
            raise PermissionDenied("Only the group owner can start an import.")
        session = stage_import(
            group=group,
            uploaded_by=request.user,
            uploaded_file=serializer.validated_data["file"],
        )
        return response.Response(
            ImportSessionSerializer(session).data,
            status=status.HTTP_201_CREATED,
        )

    @decorators.action(detail=True, methods=("get",))
    def report(self, request, pk=None):
        session = self.get_object()
        return response.Response(
            {
                "session": ImportSessionSerializer(session).data,
                "rows": ImportRowSerializer(
                    session.rows.prefetch_related("issues"),
                    many=True,
                ).data,
            }
        )


class ImportIssueViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ImportIssue.objects.select_related("session__group", "row")
    serializer_class = ImportIssueSerializer
    http_method_names = ("get", "patch", "head", "options")

    def get_queryset(self):
        return self.queryset.filter(session__group__owner=self.request.user)
