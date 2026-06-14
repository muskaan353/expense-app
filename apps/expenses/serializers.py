from rest_framework import serializers

from apps.accounts.models import User
from apps.expenses.models import ExchangeRate, Expense, ExpenseSplit
from apps.groups.models import Group


class ExchangeRateSerializer(serializers.ModelSerializer):
    source_currency = serializers.CharField(max_length=3)
    target_currency = serializers.CharField(max_length=3)

    class Meta:
        model = ExchangeRate
        fields = "__all__"
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        attrs["source_currency"] = attrs["source_currency"].upper()
        attrs["target_currency"] = attrs["target_currency"].upper()
        if attrs["source_currency"] == attrs["target_currency"]:
            raise serializers.ValidationError(
                "Source and target currencies must differ."
            )
        return attrs


class ExpenseSplitInputSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        source="user",
        queryset=User.objects.all(),
    )
    value = serializers.DecimalField(
        max_digits=14,
        decimal_places=4,
        required=False,
    )


class ExpenseSplitSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    user_display_name = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = ExpenseSplit
        fields = ("id", "user_id", "user_display_name", "base_amount", "input_value")


class ExpenseSerializer(serializers.ModelSerializer):
    group_id = serializers.PrimaryKeyRelatedField(
        source="group",
        queryset=Group.objects.all(),
        write_only=True,
    )
    paid_by_id = serializers.PrimaryKeyRelatedField(
        source="paid_by",
        queryset=User.objects.all(),
        write_only=True,
    )
    exchange_rate_id = serializers.PrimaryKeyRelatedField(
        source="exchange_rate",
        queryset=ExchangeRate.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )
    splits = ExpenseSplitInputSerializer(many=True, write_only=True)
    currency = serializers.CharField(max_length=3)
    split_details = ExpenseSplitSerializer(source="splits", many=True, read_only=True)

    class Meta:
        model = Expense
        fields = (
            "id",
            "group_id",
            "description",
            "amount",
            "currency",
            "base_amount",
            "exchange_rate_id",
            "paid_by_id",
            "split_type",
            "incurred_at",
            "notes",
            "status",
            "created_by_id",
            "created_at",
            "updated_at",
            "splits",
            "split_details",
        )
        read_only_fields = (
            "id",
            "base_amount",
            "status",
            "created_by_id",
            "created_at",
            "updated_at",
        )

    def validate_currency(self, value):
        return value.upper()


class ExpenseReadSerializer(serializers.ModelSerializer):
    splits = ExpenseSplitSerializer(many=True, read_only=True)

    class Meta:
        model = Expense
        fields = (
            "id",
            "group_id",
            "description",
            "amount",
            "currency",
            "base_amount",
            "exchange_rate_id",
            "paid_by_id",
            "split_type",
            "incurred_at",
            "notes",
            "status",
            "created_by_id",
            "created_at",
            "updated_at",
            "splits",
        )
