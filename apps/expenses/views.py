from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, response, status, viewsets

from apps.expenses.models import ExchangeRate, Expense
from apps.expenses.serializers import (
    ExchangeRateSerializer,
    ExpenseReadSerializer,
    ExpenseSerializer,
)
from apps.expenses.services import create_expense


class ExchangeRateViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer


class ExpenseViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Expense.objects.select_related("group", "paid_by", "exchange_rate")

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
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        return queryset.prefetch_related("splits__user")

    def get_serializer_class(self):
        return ExpenseSerializer if self.action == "create" else ExpenseReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        expense = create_expense(
            created_by=request.user,
            splits=data.pop("splits"),
            **data,
        )
        return response.Response(
            ExpenseReadSerializer(expense).data,
            status=status.HTTP_201_CREATED,
        )
