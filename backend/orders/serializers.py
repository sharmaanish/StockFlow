from rest_framework import serializers
# Import DRF's serializer classes.
# These help us convert JSON ↔ Python data
# and validate incoming API data.
from .models import Order, OrderItem

class OrderItemInputSerializer(serializers.Serializer):
    # This describes ONE product line coming into an order.
    #
    # Example JSON:
    #
    # {
    #     "product": "75af62f0-73a4-4bbb-9632-d06934f0f079",
    #     "quantity": 2
    # }

    product = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)

class OrderCreateSerializer(serializers.Serializer):
    # This describes the complete incoming "create order" request.
    #
    # Example:
    #
    # {
    #     "customer": "87174bcf-1e95-4eb0-9789-e88318dda4fe",
    #     "items": [
    #         {
    #             "product": "75af62f0-73a4-4bbb-9632-d06934f0f079",
    #             "quantity": 2
    #         }
    #     ]
    # }

    customer = serializers.UUIDField()
    # Receive the customer's UUID.

    items = OrderItemInputSerializer(
        many=True,
        allow_empty=False,
    )
    # Receive a list of order items.
    #
    # many=True:
    # "items" contains multiple OrderItem objects.
    #
    # allow_empty=False:
    # An order cannot be created with zero items.

class OrderItemResponseSerializer(serializers.ModelSerializer):
    product = serializers.UUIDField(source="product.id")

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "quantity",
            "unit_price",
        ]

class OrderResponseSerializer(serializers.ModelSerializer):
    items = OrderItemResponseSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "status",
            "total_amount",
            "created_at",
            "updated_at",
            "items",
        ]