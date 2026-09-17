from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product
from customers.models import Customer

from .serializers import OrderCreateSerializer
from .services import create_order


class OrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        # Validate the incoming JSON.
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer_id = serializer.validated_data["customer"]
        item_data = serializer.validated_data["items"]

        # Convert customer UUID into a Customer object.
        # customer = Customer.objects.get(id=customer_id)
        from django.shortcuts import get_object_or_404
        customer = get_object_or_404(Customer, id=customer_id)
        service_items = []

        # Convert product UUIDs into Product objects.
        for item in item_data:
            # product = Product.objects.get(id=item["product"])
            product = get_object_or_404(
                Product,
                id=item["product"],
            )
            service_items.append(
                {
                    "product": product,
                    "quantity": item["quantity"],
                }
            )

        try:
            # Business rules and inventory reservation happen in the service.
            order = create_order(
                tenant=customer.tenant,
                customer=customer,
                items=service_items,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(order.id),
                "customer": str(order.customer_id),
                "status": order.status,
                "total_amount": str(order.total_amount),
            },
            status=status.HTTP_201_CREATED,
        )
