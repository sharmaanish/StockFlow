from decimal import Decimal

from rest_framework.test import APITestCase

from catalog.models import Product
from customers.models import Customer
from inventory.models import Inventory
from tenants.models import Tenant


class OrderAPITestCase(APITestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
        )

        self.customer = Customer.objects.create(
            tenant=self.tenant,
            name="Test Customer",
        )

        self.product = Product.objects.create(
            tenant=self.tenant,
            sku="TEST-001",
            name="Test Product",
            price=Decimal("100.00"),
        )

        self.inventory = Inventory.objects.create(
            product=self.product,
            quantity=10,
        )

    def test_create_order(self):
        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.id),
                "items": [
                    {
                        "product": str(self.product.id),
                        "quantity": 2,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["total_amount"], "200.00")

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved_quantity,
            2,
        )

    def test_create_order_with_insufficient_inventory(self):
        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.id),
                "items": [
                    {
                        "product": str(self.product.id),
                        "quantity": 11,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved_quantity,
            0,
        )

    def test_create_order_with_missing_customer(self):
        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": "00000000-0000-0000-0000-000000000000",
                "items": [
                    {
                        "product": str(self.product.id),
                        "quantity": 1,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)

    def test_create_order_with_missing_product(self):
        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.id),
                "items": [
                    {
                        "product": "00000000-0000-0000-0000-000000000000",
                        "quantity": 1,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)

    def test_create_order_with_duplicate_product(self):
        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.id),
                "items": [
                    {
                        "product": str(self.product.id),
                        "quantity": 2,
                    },
                    {
                        "product": str(self.product.id),
                        "quantity": 3,
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved_quantity,
            0,
        )