from rest_framework import decorators, response, viewsets

from apps.groups.models import Group
from apps.groups.serializers import GroupSerializer
from apps.groups.services import archive_group, create_group


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.select_related("owner")
    serializer_class = GroupSerializer
    http_method_names = ("get", "post", "put", "patch", "head", "options")

    def get_queryset(self):
        return Group.objects.filter(owner=self.request.user).select_related("owner")

    def perform_create(self, serializer):
        self.instance = create_group(
            owner=self.request.user,
            **serializer.validated_data,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return response.Response(
            self.get_serializer(self.instance).data,
            status=201,
        )

    @decorators.action(detail=True, methods=("post",))
    def archive(self, request, pk=None):
        group = archive_group(group=self.get_object())
        return response.Response(self.get_serializer(group).data)
