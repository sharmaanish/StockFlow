from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
)

from accounts.permissions import IsReadOnly, IsStaff
from catalog.models import Product
from customers.models import Customer
from orders.models import Order

from .serializers import (
    OrderCreateSerializer,
    OrderResponseSerializer,
)

from .services import (
    cancel_order,
    confirm_order,
    create_order,
    deliver_order,
    ship_order,
    start_processing_order,
)


class OrderPagination(PageNumberPagination):
    """
    Controls pagination for the order list endpoint.

    Default:
        20 orders per page.
    """

    page_size = 20


class OrderListCreateAPIView(APIView):
    pagination_class = OrderPagination

    def get_permissions(self):
        """
        Apply different permissions based on the HTTP method.

        GET:
            All authenticated roles, including Viewer.

        POST:
            Admin, Manager, and Staff.
        """

        if self.request.method == "GET":
            return [IsReadOnly()]

        if self.request.method == "POST":
            return [IsStaff()]

        return [IsAuthenticated()]

    @extend_schema(
        tags=["Orders"],
        summary="List orders",
        description=(
            "Returns orders belonging to the authenticated user's tenant. "
            "Supports pagination, status filtering, searching, and ordering."
        ),
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Filter orders by status. "
                    "Use a valid Order status value."
                ),
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Search by order ID, customer ID, "
                    "customer name, or customer email."
                ),
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Sort by created_at or total_amount. "
                    "Prefix the field with '-' for descending order."
                ),
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Page number for paginated results.",
            ),
        ],
        responses=OrderResponseSerializer(many=True),
    )
    def get(self, request):
        """
        List orders belonging to the authenticated user's tenant.

        Supports:
        - Pagination
        - Status filtering
        - Searching
        - Ordering
        """

        tenant = request.user.tenant

        # Only return orders belonging to the authenticated user's
        # tenant. This maintains tenant isolation.
        orders = (
            Order.objects
            .filter(tenant=tenant)
            .prefetch_related("items")
            .order_by("-created_at")
        )

        # ---------------------------------------------------------
        # Status filtering
        # ---------------------------------------------------------
        status_filter = request.query_params.get("status")

        if status_filter:
            valid_statuses = {
                choice.value
                for choice in Order.Status
            }

            if status_filter not in valid_statuses:
                return Response(
                    {
                        "detail": (
                            f"Invalid status '{status_filter}'. "
                            f"Valid statuses are: "
                            f"{', '.join(sorted(valid_statuses))}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            orders = orders.filter(
                status=status_filter
            )

        # ---------------------------------------------------------
        # Searching
        # ---------------------------------------------------------
        search = request.query_params.get("search")

        if search:
            orders = orders.filter(
                Q(id__icontains=search)
                | Q(customer__id__icontains=search)
                | Q(customer__name__icontains=search)
                | Q(customer__email__icontains=search)
            )

        # ---------------------------------------------------------
        # Ordering
        # ---------------------------------------------------------
        ordering = request.query_params.get("ordering")

        if ordering:
            allowed_ordering_fields = {
                "created_at",
                "total_amount",
            }

            ordering_field = ordering.lstrip("-")

            if ordering_field not in allowed_ordering_fields:
                return Response(
                    {
                        "detail": (
                            f"Invalid ordering field "
                            f"'{ordering_field}'. "
                            f"Allowed fields are: "
                            f"{', '.join(sorted(allowed_ordering_fields))}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            orders = orders.order_by(ordering)

        # ---------------------------------------------------------
        # Pagination
        # ---------------------------------------------------------
        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            orders,
            request,
            view=self,
        )

        serializer = OrderResponseSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    @extend_schema(
        tags=["Orders"],
        summary="Create an order",
        description=(
            "Creates a new order for the authenticated user's tenant."
        ),
        request=OrderCreateSerializer,
        responses={
            201: OrderResponseSerializer,
            400: None,
        },
    )
    def post(self, request):
        """
        Create a new order for the authenticated user's tenant.
        """

        serializer = OrderCreateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        tenant = request.user.tenant

        customer = get_object_or_404(
            Customer,
            id=serializer.validated_data["customer"],
        )

        items = []

        for item in serializer.validated_data["items"]:
            product = get_object_or_404(
                Product,
                id=item["product"],
            )

            items.append(
                {
                    "product": product,
                    "quantity": item["quantity"],
                }
            )

        try:
            order = create_order(
                tenant=tenant,
                customer=customer,
                items=items,
                user=request.user,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = OrderResponseSerializer(
            order,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class OrderRetrieveAPIView(APIView):
    """
    Retrieve a single order belonging to the authenticated
    user's tenant.
    """

    permission_classes = [IsReadOnly]

    @extend_schema(
        tags=["Orders"],
        summary="Retrieve an order",
        description=(
            "Returns a single order belonging to the "
            "authenticated user's tenant."
        ),
        parameters=[
            OpenApiParameter(
                name="order_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                required=True,
                description="UUID of the order to retrieve.",
            ),
        ],
        responses={
            200: OrderResponseSerializer,
            404: None,
        },
    )
    def get(self, request, order_id):
        tenant = request.user.tenant

        # Read access must remain tenant-scoped.
        order = get_object_or_404(
            Order,
            id=order_id,
            tenant=tenant,
        )

        serializer = OrderResponseSerializer(
            order,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class OrderConfirmAPIView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(
        tags=["Orders"],
        summary="Confirm an order",
        description=(
            "Confirms an order using the order lifecycle service. "
            "Requires Staff, Manager, or Admin access."
        ),
        parameters=[
            OpenApiParameter(
                name="order_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                required=True,
                description="UUID of the order to confirm.",
            ),
        ],
        request=None,
        responses={
            200: OrderResponseSerializer,
            400: None,
            404: None,
        },
    )
    def post(self, request, order_id):
        tenant = request.user.tenant

        # Fetch by ID first so the service layer can explicitly
        # validate tenant ownership.
        order = get_object_or_404(
            Order,
            id=order_id,
        )

        try:
            order = confirm_order(
                order=order,
                tenant=tenant,
                user=request.user,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderResponseSerializer(
            order,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class OrderCancelAPIView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(
        tags=["Orders"],
        summary="Cancel an order",
        description=(
            "Cancels an order using the order lifecycle service. "
            "Requires Staff, Manager, or Admin access."
        ),
        parameters=[
            OpenApiParameter(
                name="order_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                required=True,
                description="UUID of the order to cancel.",
            ),
        ],
        request=None,
        responses={
            200: OrderResponseSerializer,
            400: None,
            404: None,
        },
    )
    def post(self, request, order_id):
        tenant = request.user.tenant

        # Fetch by ID first so the service layer can explicitly
        # validate tenant ownership.
        order = get_object_or_404(
            Order,
            id=order_id,
        )

        try:
            order = cancel_order(
                order=order,
                tenant=tenant,
                user=request.user,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderResponseSerializer(
            order,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class OrderStartProcessingAPIView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(
        tags=["Orders"],
        summary="Start order processing",
        description=(
            "Moves an order into processing using the order "
            "lifecycle service. Requires Staff, Manager, or Admin access."
        ),
        parameters=[
            OpenApiParameter(
                name="order_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                required=True,
                description="UUID of the order to start processing.",
            ),
        ],
        request=None,
        responses={
            200: OrderResponseSerializer,
            400: None,
            404: None,
        },
    )
    def post(self, request, order_id):
        tenant = request.user.tenant

        # Fetch by ID first so the service layer can explicitly
        # validate tenant ownership.
        order = get_object_or_404(
            Order,
            id=order_id,
        )

        try:
            order = start_processing_order(
                order=order,
                tenant=tenant,
                user=request.user,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderResponseSerializer(
            order,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class OrderShipAPIView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(
        tags=["Orders"],
        summary="Ship an order",
        description=(
            "Moves an order to the shipped state using the order "
            "lifecycle service. Requires Staff, Manager, or Admin access."
        ),
        parameters=[
            OpenApiParameter(
                name="order_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                required=True,
                description="UUID of the order to ship.",
            ),
        ],
        request=None,
        responses={
            200: OrderResponseSerializer,
            400: None,
            404: None,
        },
    )
    def post(self, request, order_id):
        tenant = request.user.tenant

        # Fetch by ID first so ship_order() can perform the
        # tenant ownership validation.
        order = get_object_or_404(
            Order,
            id=order_id,
        )

        try:
            order = ship_order(
                order=order,
                tenant=tenant,
                user=request.user,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderResponseSerializer(
            order,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class OrderDeliverAPIView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(
        tags=["Orders"],
        summary="Deliver an order",
        description=(
            "Marks an order as delivered using the order "
            "lifecycle service. Requires Staff, Manager, or Admin access."
        ),
        parameters=[
            OpenApiParameter(
                name="order_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                required=True,
                description="UUID of the order to deliver.",
            ),
        ],
        request=None,
        responses={
            200: OrderResponseSerializer,
            400: None,
            404: None,
        },
    )
    def post(self, request, order_id):
        tenant = request.user.tenant

        # Fetch by ID first so deliver_order() can perform the
        # tenant ownership validation.
        order = get_object_or_404(
            Order,
            id=order_id,
        )

        try:
            order = deliver_order(
                order=order,
                tenant=tenant,
                user=request.user,
            )

        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderResponseSerializer(
            order,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )