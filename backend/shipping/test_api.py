from decimal import Decimal

from rest_framework.test import APITestCase

from accounts.models import User
from customers.models import Customer
from orders.models import Order
from shipping.models import Shipment
from tenants.models import Tenant


class ShipmentAPITestCase(APITestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
        )

        self.user = User.objects.create_user(
            tenant=self.tenant,
            email="shipping-api@example.com",
            password="test-password",
        )

        self.customer = Customer.objects.create(
            tenant=self.tenant,
            name="Test Customer",
        )

        self.order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PROCESSING,
            total_amount=Decimal("500.00"),
        )

        self.client.force_authenticate(
            user=self.user,
        )

    def test_create_shipment(self):
        response = self.client.post(
            "/api/v1/shipments/",
            {
                "order": str(self.order.id),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["order"],
            str(self.order.id),
        )

        self.assertEqual(
            response.data["status"],
            Shipment.Status.PENDING,
        )

        self.assertTrue(
            Shipment.objects.filter(
                order=self.order,
            ).exists()
        )

    def test_create_shipment_requires_authentication(self):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.post(
            "/api/v1/shipments/",
            {
                "order": str(self.order.id),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_create_shipment_rejects_wrong_tenant(self):
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        other_customer = Customer.objects.create(
            tenant=other_tenant,
            name="Other Customer",
        )

        other_order = Order.objects.create(
            tenant=other_tenant,
            customer=other_customer,
            status=Order.Status.PROCESSING,
            total_amount=Decimal("500.00"),
        )

        response = self.client.post(
            "/api/v1/shipments/",
            {
                "order": str(other_order.id),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            Shipment.objects.filter(
                order=other_order,
            ).exists()
        )

    def test_create_shipment_rejects_invalid_order_status(self):
        self.order.status = Order.Status.PENDING
        self.order.save()

        response = self.client.post(
            "/api/v1/shipments/",
            {
                "order": str(self.order.id),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            Shipment.objects.filter(
                order=self.order,
            ).exists()
        )

    def test_create_shipment_rejects_duplicate(self):
        Shipment.objects.create(
            tenant=self.tenant,
            order=self.order,
        )

        response = self.client.post(
            "/api/v1/shipments/",
            {
                "order": str(self.order.id),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            Shipment.objects.filter(
                order=self.order,
            ).count(),
            1,
        )

    def test_update_shipment_status(self):
        shipment = Shipment.objects.create(
            tenant=self.tenant,
            order=self.order,
        )

        response = self.client.post(
            f"/api/v1/shipments/{shipment.id}/status/",
            {
                "status": Shipment.Status.PROCESSING,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            Shipment.Status.PROCESSING,
        )

    def test_full_shipment_lifecycle(self):
        shipment = Shipment.objects.create(
            tenant=self.tenant,
            order=self.order,
        )

        statuses = [
            Shipment.Status.PROCESSING,
            Shipment.Status.SHIPPED,
            Shipment.Status.IN_TRANSIT,
            Shipment.Status.DELIVERED,
        ]

        for shipment_status in statuses:
            response = self.client.post(
                f"/api/v1/shipments/{shipment.id}/status/",
                {
                    "status": shipment_status,
                },
                format="json",
            )

            self.assertEqual(
                response.status_code,
                200,
            )

            self.assertEqual(
                response.data["status"],
                shipment_status,
            )

    def test_invalid_status_transition(self):
        shipment = Shipment.objects.create(
            tenant=self.tenant,
            order=self.order,
        )

        response = self.client.post(
            f"/api/v1/shipments/{shipment.id}/status/",
            {
                "status": Shipment.Status.DELIVERED,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_cross_tenant_status_update_rejected(self):
        shipment = Shipment.objects.create(
            tenant=self.tenant,
            order=self.order,
        )

        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        other_user = User.objects.create_user(
            tenant=other_tenant,
            email="other-shipping@example.com",
            password="test-password",
        )

        self.client.force_authenticate(
            user=other_user,
        )

        response = self.client.post(
            f"/api/v1/shipments/{shipment.id}/status/",
            {
                "status": Shipment.Status.PROCESSING,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_retrieve_shipment(self):
        shipment = Shipment.objects.create(
            tenant=self.tenant,
            order=self.order,
        )

        response = self.client.get(
            f"/api/v1/shipments/{shipment.id}/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            str(shipment.id),
        )

        self.assertEqual(
            response.data["order"],
            str(self.order.id),
        )

    def test_retrieve_shipment_rejects_other_tenant(self):
        shipment = Shipment.objects.create(
            tenant=self.tenant,
            order=self.order,
        )

        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        other_user = User.objects.create_user(
            tenant=other_tenant,
            email="other-retrieve@example.com",
            password="test-password",
        )

        self.client.force_authenticate(
            user=other_user,
        )

        response = self.client.get(
            f"/api/v1/shipments/{shipment.id}/",
        )

        self.assertEqual(
            response.status_code,
            404,
        )