from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.models import Product
from customers.models import Customer
from inventory.models import Inventory
from tenants.models import Tenant
from orders.models import Order
from orders.services import create_order

class CreateOrderTests(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
        )

        self.customer = Customer.objects.create(
            tenant=self.tenant,
            name="Test Customer",
            email="test@example.com",
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
            reserved_quantity=0,
        )

        self.product_2 = Product.objects.create(
            tenant=self.tenant,
            sku="TEST-002",
            name="Second Test Product",
            price=Decimal("50.00"),
        )

        self.inventory_2 = Inventory.objects.create(
            product=self.product_2,
            quantity=20,
            reserved_quantity=0,
        )

    def test_create_order_reserves_inventory(self):
        order = create_order(
            tenant=self.tenant,
            customer=self.customer,
            items=[
                {
                    "product": self.product,
                    "quantity": 3,
                }
            ],
        )

        self.inventory.refresh_from_db()

        self.assertEqual(
            order.total_amount,
            Decimal("300.00"),
        )

        self.assertEqual(
            order.items.count(),
            1,
        )

        self.assertEqual(
            self.inventory.reserved_quantity,
            3,
        )

        self.assertEqual(
            self.inventory.quantity
            - self.inventory.reserved_quantity,
            7,
        )

    def test_create_order_rejects_insufficient_inventory(self):
        with self.assertRaises(ValidationError):
            create_order(
                tenant=self.tenant,
                customer=self.customer,
                items=[
                    {
                        "product": self.product,
                        "quantity": 11,
                    }
                ],
            )

    def test_create_order_rolls_back_on_insufficient_inventory(self):
        with self.assertRaises(ValidationError):
            create_order(
                tenant=self.tenant,
                customer=self.customer,
                items=[
                    {
                        "product": self.product,
                        "quantity": 11,
                    }
                ],
            )

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved_quantity,
            0,
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

    def test_create_order_with_multiple_product(self):
        order = create_order(
            tenant=self.tenant,
            customer=self.customer,
            items=[
                {
                    "product": self.product,
                    "quantity": 3,
                },
                {
                    "product": self.product_2,
                    "quantity": 4,
                },
            ],
        )

        self.inventory.refresh_from_db()
        self.inventory_2.refresh_from_db()

        self.assertEqual(
            order.total_amount,
            Decimal("500.00"),
        )

        self.assertEqual(
            order.items.count(),
            2,
        )

        self.assertEqual(
            self.inventory.reserved_quantity,
            3,
        )

        self.assertEqual(
            self.inventory_2.reserved_quantity,
            4,
        )

    def test_create_order_rejects_duplicate_products(self):
        with self.assertRaises(ValidationError):
            create_order(
                tenant=self.tenant,
                customer=self.customer,
                items=[
                    {
                        "product": self.product,
                        "quantity": 2,
                    },
                    {
                        "product": self.product,
                        "quantity": 3,
                    },
                ],
            )

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved_quantity,
            0,
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )