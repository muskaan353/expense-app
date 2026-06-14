from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, response, status, viewsets

from apps.settlements.models import Settlement
from apps.settlements.serializers import SettlementReadSerializer, SettlementSerializer
from apps.settlements.services import create_settlement


class SettlementViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Settlement.objects.select_related("group", "payer", "payee")

    def get_queryset(self):
        now = timezone.now()
        queryset = self.queryset.filter(
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
        group_id = self.request.query_params.get("group_id")
        return queryset.filter(group_id=group_id) if group_id else queryset

    def get_serializer_class(self):
        return SettlementSerializer if self.action == "create" else SettlementReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        settlement = create_settlement(
            created_by=request.user,
            **serializer.validated_data,
        )
        return response.Response(
            SettlementReadSerializer(settlement).data,
            status=status.HTTP_201_CREATED,
        )
