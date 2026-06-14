from rest_framework import serializers

from apps.groups.models import Group
from apps.imports.models import ImportIssue, ImportRow, ImportSession


class ImportSessionCreateSerializer(serializers.Serializer):
    group_id = serializers.PrimaryKeyRelatedField(
        source="group",
        queryset=Group.objects.all(),
    )
    file = serializers.FileField()


class ImportIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportIssue
        fields = "__all__"
        read_only_fields = (
            "id",
            "session",
            "row",
            "row_number",
            "issue_code",
            "severity",
            "field_name",
            "message",
            "raw_value",
            "proposed_action",
            "created_at",
        )


class ImportRowSerializer(serializers.ModelSerializer):
    issues = ImportIssueSerializer(many=True, read_only=True)

    class Meta:
        model = ImportRow
        fields = (
            "id",
            "row_number",
            "raw_data",
            "normalized_data",
            "status",
            "issues",
        )


class ImportSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportSession
        fields = (
            "id",
            "group_id",
            "uploaded_by_id",
            "original_filename",
            "checksum_sha256",
            "status",
            "row_count",
            "issue_count",
            "report",
            "created_at",
            "completed_at",
        )
