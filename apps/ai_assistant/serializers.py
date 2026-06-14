from rest_framework import serializers

from apps.groups.models import Group


class AssistantQuerySerializer(serializers.Serializer):
    group_id = serializers.PrimaryKeyRelatedField(
        source="group",
        queryset=Group.objects.all(),
    )
    question = serializers.CharField(max_length=500)


class AssistantCitationSerializer(serializers.Serializer):
    kind = serializers.CharField()
    reference_id = serializers.IntegerField()


class AssistantResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()
    data = serializers.JSONField()
    citations = AssistantCitationSerializer(many=True)
    generated_from = serializers.CharField()
