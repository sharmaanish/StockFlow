from rest_framework.test import APITestCase

from accounts.models import User
from customers.models import Customer
from orders.models import Order
from shipping.models import Shipment
from shipping.services import (
    create_shipment,
    update_shipment_status,
)
from tenants.models import Tenant


class ShipmentServiceTestCase(APITestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
        )

        self.user = User.objects.create_user(
            tenant=self.tenant,
            email="shipping-test@example.com",
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
            total_amount="500.00",
        )

    def test_create_shipment(self):
        shipment = create_shipment(
            tenant=self.tenant,
            order=self.order,
        )

        self.assertEqual(
            shipment.status,
            Shipment.Status.PENDING,
        )

        self.assertEqual(
            shipment.order,
            self.order,
        )

    def test_create_shipment_rejects_wrong_tenant(self):
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        with self.assertRaisesMessage(
            Exception,
            "Order does not belong to this tenant.",
        ):
            create_shipment(
                tenant=other_tenant,
                order=self.order,
            )

    def test_create_shipment_rejects_duplicate(self):
        create_shipment(
            tenant=self.tenant,
            order=self.order,
        )

        with self.assertRaises(Exception):
            create_shipment(
                tenant=self.tenant,
                order=self.order,
            )

    def test_create_shipment_rejects_invalid_order_status(self):
        self.order.status = Order.Status.PENDING
        self.order.save()

        with self.assertRaisesMessage(
            Exception,
            "Shipment can only be created for a processing or shipped order.",
        ):
            create_shipment(
                tenant=self.tenant,
                order=self.order,
            )

    def test_update_shipment_status(self):
        shipment = create_shipment(
            tenant=self.tenant,
            order=self.order,
        )

        shipment = update_shipment_status(
            shipment=shipment,
            tenant=self.tenant,
            status=Shipment.Status.PROCESSING,
        )

        self.assertEqual(
            shipment.status,
            Shipment.Status.PROCESSING,
        )

    def test_full_shipment_lifecycle(self):
        shipment = create_shipment(
            tenant=self.tenant,
            order=self.order,
        )

        for status in [
            Shipment.Status.PROCESSING,
            Shipment.Status.SHIPPED,
            Shipment.Status.IN_TRANSIT,
            Shipment.Status.DELIVERED,
        ]:
            shipment = update_shipment_status(
                shipment=shipment,
                tenant=self.tenant,
                status=status,
            )

        self.assertEqual(
            shipment.status,
            Shipment.Status.DELIVERED,
        )

    def test_invalid_status_transition(self):
        shipment = create_shipment(
            tenant=self.tenant,
            order=self.order,
        )

        with self.assertRaisesMessage(
            Exception,
            "Cannot change shipment status",
        ):
            update_shipment_status(
                shipment=shipment,
                tenant=self.tenant,
                status=Shipment.Status.DELIVERED,
            )

    def test_cross_tenant_status_update_rejected(self):
        shipment = create_shipment(
            tenant=self.tenant,
            order=self.order,
        )

        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        with self.assertRaisesMessage(
            Exception,
            "Shipment does not belong to this tenant.",
        ):
            update_shipment_status(
                shipment=shipment,
                tenant=other_tenant,
                status=Shipment.Status.PROCESSING,
            )