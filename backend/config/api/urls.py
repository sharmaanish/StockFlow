from django.urls import path

from .views import health_check, me

from orders.views import (
    OrderListCreateAPIView,
    OrderCancelAPIView,
    OrderConfirmAPIView,
    OrderStartProcessingAPIView,
    OrderShipAPIView,
    OrderDeliverAPIView,
    OrderRetrieveAPIView,
)
from payments.views import PaymentCreateAPIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
)


urlpatterns = [

    path(
        "health/",
        health_check,
        name="health-check",
    ),

    # GET  /api/v1/orders/
    # POST /api/v1/orders/
    path(
        "orders/",
        OrderListCreateAPIView.as_view(),
        name="order-list-create",
    ),

    path(
        "auth/token/",
        TokenObtainPairView.as_view(),
        name="token-obtain-pair",
    ),

    path(
        "auth/me/",
        me,
        name="auth-me",
    ),

    path(
        "orders/<uuid:order_id>/cancel/",
        OrderCancelAPIView.as_view(),
        name="order-cancel",
    ),

    path(
        "orders/<uuid:order_id>/confirm/",
        OrderConfirmAPIView.as_view(),
        name="order-confirm",
    ),

    path(
        "orders/<uuid:order_id>/processing/",
        OrderStartProcessingAPIView.as_view(),
        name="order-start-processing",
    ),

    path(
        "orders/<uuid:order_id>/ship/",
        OrderShipAPIView.as_view(),
        name="order-ship",
    ),

    path(
        "orders/<uuid:order_id>/deliver/",
        OrderDeliverAPIView.as_view(),
        name="order-deliver",
    ),

    path(
        "orders/<uuid:order_id>/",
        OrderRetrieveAPIView.as_view(),
        name="order-detail",
    ),
    path(
    "payments/",
    PaymentCreateAPIView.as_view(),
    name="payment-create",
),
]