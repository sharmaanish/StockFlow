from rest_framework import serializers

from payments.models import Payment


class PaymentCreateSerializer(serializers.Serializer):
    order = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    method = serializers.ChoiceField(
        choices=Payment.Method.choices,
    )


class PaymentResponseSerializer(serializers.ModelSerializer):
    order = serializers.UUIDField(source="order.id")

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "amount",
            "status",
            "method",
            "transaction_id",
            "created_at",
            "updated_at",
        ]