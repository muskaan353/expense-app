from rest_framework import serializers

from apps.accounts.models import User
from apps.groups.models import Group, GroupMembership


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


class GroupMembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        source="user",
        queryset=User.objects.all(),
    )
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_display_name = serializers.CharField(
        source="user.display_name",
        read_only=True,
    )

    class Meta:
        model = GroupMembership
        fields = (
            "id",
            "group_id",
            "user_id",
            "user_email",
            "user_display_name",
            "role",
            "joined_at",
            "left_at",
            "created_at",
        )
        read_only_fields = (
            "id",
            "group_id",
            "user_email",
            "user_display_name",
            "created_at",
        )

    def validate(self, attrs):
        joined_at = attrs.get("joined_at")
        left_at = attrs.get("left_at")
        if left_at and joined_at and left_at <= joined_at:
            raise serializers.ValidationError(
                {"left_at": "left_at must be after joined_at."}
            )
        if attrs.get("role") == GroupMembership.Role.OWNER:
            raise serializers.ValidationError(
                {"role": "A group can only have its original owner."}
            )
        return attrs


class LeaveMembershipSerializer(serializers.Serializer):
    left_at = serializers.DateTimeField()
