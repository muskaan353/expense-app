from rest_framework import serializers

from apps.accounts.models import User
from apps.expenses.models import ExchangeRate
from apps.groups.models import Group
from apps.settlements.models import Settlement


class SettlementSerializer(serializers.ModelSerializer):
    group_id = serializers.PrimaryKeyRelatedField(
        source="group",
        queryset=Group.objects.all(),
    )
    payer_id = serializers.PrimaryKeyRelatedField(
        source="payer",
        queryset=User.objects.all(),
    )
    payee_id = serializers.PrimaryKeyRelatedField(
        source="payee",
        queryset=User.objects.all(),
    )
    exchange_rate_id = serializers.PrimaryKeyRelatedField(
        source="exchange_rate",
        queryset=ExchangeRate.objects.all(),
        allow_null=True,
        required=False,
    )
    currency = serializers.CharField(max_length=3)

    class Meta:
        model = Settlement
        fields = (
            "id",
            "group_id",
            "payer_id",
            "payee_id",
            "amount",
            "currency",
            "base_amount",
            "exchange_rate_id",
            "settled_at",
            "note",
            "created_by_id",
            "created_at",
        )
        read_only_fields = ("id", "base_amount", "created_by_id", "created_at")

    def validate_currency(self, value):
        return value.upper()

    def validate(self, attrs):
        if attrs["payer"] == attrs["payee"]:
            raise serializers.ValidationError("Payer and payee must differ.")
        return attrs


class SettlementReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settlement
        fields = (
            "id",
            "group_id",
            "payer_id",
            "payee_id",
            "amount",
            "currency",
            "base_amount",
            "exchange_rate_id",
            "settled_at",
            "note",
            "created_by_id",
            "created_at",
        )
