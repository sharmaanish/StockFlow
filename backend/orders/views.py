from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product
from customers.models import Customer
from orders.models import Order
from .serializers import OrderResponseSerializer
from .serializers import OrderCreateSerializer
from .services import (
    cancel_order,
    confirm_order,
    create_order,
    deliver_order,
    ship_order,
    start_processing_order,
)


class OrderListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = request.user.tenant

        orders = (
            Order.objects
            .filter(tenant=tenant)
            .prefetch_related("items")
            .order_by("-created_at")
        )

        serializer = OrderResponseSerializer(
            orders,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = request.user.tenant

        customer_id = serializer.validated_data["customer"]
        item_data = serializer.validated_data["items"]

        customer = get_object_or_404(
            Customer,
            id=customer_id,
        )

        service_items = []

        for item in item_data:
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
            order = create_order(
                tenant=tenant,
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


class OrderCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        tenant = request.user.tenant

        order = get_object_or_404(
            Order,
            id=order_id,
        )

        try:
            order = cancel_order(
                order=order,
                tenant=tenant,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(order.id),
                "status": order.status,
            },
            status=status.HTTP_200_OK,
        )


class OrderConfirmAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        tenant = request.user.tenant

        order = get_object_or_404(
            Order,
            id=order_id,
        )

        try:
            order = confirm_order(
                order=order,
                tenant=tenant,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(order.id),
                "status": order.status,
            },
            status=status.HTTP_200_OK,
        )


class OrderStartProcessingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        tenant = request.user.tenant

        order = get_object_or_404(
            Order,
            id=order_id,
        )

        try:
            order = start_processing_order(
                order=order,
                tenant=tenant,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(order.id),
                "status": order.status,
            },
            status=status.HTTP_200_OK,
        )


class OrderShipAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        tenant = request.user.tenant

        order = get_object_or_404(
            Order,
            id=order_id,
        )

        try:
            order = ship_order(
                order=order,
                tenant=tenant,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(order.id),
                "status": order.status,
            },
            status=status.HTTP_200_OK,
        )


class OrderDeliverAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        tenant = request.user.tenant

        order = get_object_or_404(
            Order,
            id=order_id,
        )

        try:
            order = deliver_order(
                order=order,
                tenant=tenant,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(order.id),
                "status": order.status,
            },
            status=status.HTTP_200_OK,
        )


class OrderRetrieveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        tenant = request.user.tenant

        order = get_object_or_404(
            Order,
            id=order_id,
            tenant=tenant,
        )

        serializer = OrderResponseSerializer(order)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
