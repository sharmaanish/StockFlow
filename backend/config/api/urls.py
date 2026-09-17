from django.urls import path

from .views import health_check, me
from orders.views import (
    OrderCreateAPIView,
    OrderCancelAPIView,
    OrderConfirmAPIView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
)

urlpatterns = [

    # Health-check endpoint.
    #
    # Final URL:
    # /api/v1/health/
    path(
        "health/",
        health_check,
        name="health-check",
    ),

    # Order creation endpoint.
    #
    # Final URL:
    # /api/v1/orders/
    #
    # POST requests are handled by
    # OrderCreateAPIView.post().
    path(
        "orders/",
        OrderCreateAPIView.as_view(),
        name="order-create",
    ),

    path(
        "auth/token/",
        TokenObtainPairView.as_view(),
        name="token-obtain-pair",
    ),

    # Authenticated user test endpoint.
    #
    # Final URL:
    # /api/v1/auth/me/
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
]