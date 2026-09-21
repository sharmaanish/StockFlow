from rest_framework import serializers

from audit.models import AuditLog


class AuditLogResponseSerializer(serializers.ModelSerializer):
    user = serializers.UUIDField(
        source="user.id",
        allow_null=True,
        read_only=True,
    )

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "action",
            "entity_type",
            "entity_id",
            "metadata",
            "created_at",
        ]