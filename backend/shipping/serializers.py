from rest_framework import serializers

from shipping.models import Shipment


class ShipmentCreateSerializer(serializers.Serializer):
    order = serializers.UUIDField()


class ShipmentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=Shipment.Status.choices,
    )


class ShipmentResponseSerializer(serializers.ModelSerializer):
    order = serializers.UUIDField(source="order.id")

    class Meta:
        model = Shipment
        fields = [
            "id",
            "order",
            "status",
            "carrier",
            "tracking_number",
            "created_at",
            "updated_at",
        ]