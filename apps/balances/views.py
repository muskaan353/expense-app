from drf_spectacular.utils import extend_schema
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.balances.serializers import GroupBalanceSerializer
from apps.balances.services import calculate_group_balances
from apps.groups.views import GroupViewSet


class GroupBalanceView(APIView):
    @extend_schema(responses=GroupBalanceSerializer)
    def get(self, request, group_id):
        accessible_groups = GroupViewSet()
        accessible_groups.request = request
        group = get_object_or_404(accessible_groups.get_queryset(), pk=group_id)
        data = calculate_group_balances(group=group)
        return Response(GroupBalanceSerializer(data).data)
