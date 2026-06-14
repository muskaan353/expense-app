from rest_framework import decorators, response, status, viewsets
from rest_framework.exceptions import PermissionDenied

from apps.groups.models import Group, GroupMembership
from apps.groups.permissions import IsGroupOwnerOrReadOnly
from apps.groups.selectors import accessible_groups_for
from apps.groups.serializers import (
    GroupMembershipSerializer,
    GroupSerializer,
    LeaveMembershipSerializer,
)
from apps.groups.services import (
    add_membership,
    archive_group,
    create_group,
    end_membership,
)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.select_related("owner")
    serializer_class = GroupSerializer
    permission_classes = (IsGroupOwnerOrReadOnly,)
    http_method_names = ("get", "post", "put", "patch", "head", "options")

    def get_queryset(self):
        return accessible_groups_for(user=self.request.user)

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
        self._require_owner(self.get_object())
        group = archive_group(group=self.get_object())
        return response.Response(self.get_serializer(group).data)

    @decorators.action(detail=True, methods=("get", "post"))
    def memberships(self, request, pk=None):
        group = self.get_object()
        if request.method == "GET":
            memberships = group.memberships.select_related("user")
            return response.Response(
                GroupMembershipSerializer(memberships, many=True).data
            )

        self._require_owner(group)
        serializer = GroupMembershipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        membership = add_membership(
            group=group,
            user=data["user"],
            role=data["role"],
            joined_at=data["joined_at"],
            left_at=data.get("left_at"),
        )
        return response.Response(
            GroupMembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )

    @decorators.action(
        detail=True,
        methods=("post",),
        url_path=r"memberships/(?P<membership_id>\d+)/leave",
    )
    def leave_membership(self, request, pk=None, membership_id=None):
        group = self.get_object()
        self._require_owner(group)
        serializer = LeaveMembershipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = group.memberships.get(pk=membership_id)
        membership = end_membership(
            membership=membership,
            left_at=serializer.validated_data["left_at"],
        )
        return response.Response(GroupMembershipSerializer(membership).data)

    def _require_owner(self, group):
        if group.owner_id != self.request.user.id:
            raise PermissionDenied("Only the group owner can perform this action.")
