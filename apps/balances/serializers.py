from rest_framework import serializers


class BalanceEntrySerializer(serializers.Serializer):
    kind = serializers.CharField()
    reference_id = serializers.IntegerField()
    description = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)


class MemberBalanceSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    display_name = serializers.CharField()
    balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    entries = BalanceEntrySerializer(many=True)


class DebtSerializer(serializers.Serializer):
    payer_id = serializers.IntegerField()
    payee_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)


class GroupBalanceSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    currency = serializers.CharField()
    members = MemberBalanceSerializer(many=True)
    suggested_settlements = DebtSerializer(many=True)
