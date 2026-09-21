from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from shipping.models import Shipment
from shipping.serializers import (
    ShipmentCreateSerializer,
    ShipmentResponseSerializer,
    ShipmentStatusUpdateSerializer,
)
from shipping.services import (
    create_shipment,
    update_shipment_status,
)


class ShipmentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ShipmentCreateSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        tenant = request.user.tenant

        order = get_object_or_404(
            Order,
            id=serializer.validated_data["order"],
        )

        try:
            shipment = create_shipment(
                tenant=tenant,
                order=order,
                user=request.user,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = ShipmentResponseSerializer(
            shipment,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class ShipmentStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, shipment_id):
        serializer = ShipmentStatusUpdateSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        tenant = request.user.tenant

        shipment = get_object_or_404(
            Shipment,
            id=shipment_id,
        )

        try:
            shipment = update_shipment_status(
                shipment=shipment,
                tenant=tenant,
                status=serializer.validated_data["status"],
                user=request.user,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = ShipmentResponseSerializer(
            shipment,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class ShipmentRetrieveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, shipment_id):
        tenant = request.user.tenant

        shipment = get_object_or_404(
            Shipment,
            id=shipment_id,
            tenant=tenant,
        )

        serializer = ShipmentResponseSerializer(
            shipment,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )