from rest_framework import serializers

from apps.groups.models import Group


class GroupSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(read_only=True)
    base_currency = serializers.CharField(max_length=3)

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "description",
            "base_currency",
            "owner_id",
            "created_at",
            "updated_at",
            "archived_at",
        )
        read_only_fields = (
            "id",
            "owner_id",
            "created_at",
            "updated_at",
            "archived_at",
        )

    def validate_base_currency(self, value):
        currency = value.upper()
        if not currency.isalpha():
            raise serializers.ValidationError(
                "Currency must be a three-letter ISO 4217 code."
            )
        return currency
