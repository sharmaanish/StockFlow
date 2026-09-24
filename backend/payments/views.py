from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsStaff
from orders.models import Order
from payments.serializers import (
    PaymentCreateSerializer,
    PaymentResponseSerializer,
)
from payments.services import create_payment


class PaymentCreateAPIView(APIView):
    permission_classes = [IsStaff]

    def post(self, request):
        serializer = PaymentCreateSerializer(
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
            payment = create_payment(
                tenant=tenant,
                order=order,
                amount=serializer.validated_data["amount"],
                method=serializer.validated_data["method"],
                user=request.user,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = PaymentResponseSerializer(
            payment,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )