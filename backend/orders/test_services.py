from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.models import Product
from customers.models import Customer
from inventory.models import Inventory
from tenants.models import Tenant
from orders.models import Order, OrderItem
from orders.services import (
    cancel_order,
    create_order,
    confirm_order,
    start_processing_order,
    ship_order,
    deliver_order,
)

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

    def test_create_order_rejects_customer_from_different_tenant(self):
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        other_customer = Customer.objects.create(
            tenant=other_tenant,
            name="Other Customer",
            email="other@example.com",
        )

        with self.assertRaises(ValidationError):
            create_order(
                tenant=self.tenant,
                customer=other_customer,
                items=[
                    {
                        "product": self.product,
                        "quantity": 1,
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

    def test_create_order_rejects_product_from_different_tenant(self):
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        other_product = Product.objects.create(
            tenant=other_tenant,
            sku="OTHER-001",
            name="Other Product",
            price=Decimal("75.00"),
        )

        Inventory.objects.create(
            product=other_product,
            quantity=10,
            reserved_quantity=0,
        )

        with self.assertRaises(ValidationError):
            create_order(
                tenant=self.tenant,
                customer=self.customer,
                items=[
                    {
                        "product": other_product,
                        "quantity": 1,
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

    def test_create_order_rejects_inactive_customer(self):
        self.customer.is_active = False
        self.customer.save(update_fields=["is_active"])

        with self.assertRaises(ValidationError):
            create_order(
                tenant=self.tenant,
                customer=self.customer,
                items=[
                    {
                        "product": self.product,
                        "quantity": 1,
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

    def test_create_order_rejects_inactive_product(self):
        self.product.is_active = False
        self.product.save(update_fields=["is_active"])

        with self.assertRaises(ValidationError):
            create_order(
                tenant=self.tenant,
                customer=self.customer,
                items=[
                    {
                        "product": self.product,
                        "quantity": 1,
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

    def test_create_order_rejects_empty_items(self):
        with self.assertRaises(ValidationError):
            create_order(
                tenant=self.tenant,
                customer=self.customer,
                items=[],
            )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

    def test_confirm_pending_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
        )

        confirmed_order = confirm_order(
            order=order,
            tenant=self.tenant,
        )

        self.assertEqual(
            confirmed_order.status,
            Order.Status.CONFIRMED,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )

    def test_cannot_confirm_non_pending_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.CONFIRMED,
        )

        with self.assertRaises(ValidationError):
            confirm_order(
                order=order,
                tenant=self.tenant,
            )

    def test_cannot_confirm_order_from_another_tenant(self):
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        order = Order.objects.create(
            tenant=other_tenant,
            customer=self.customer,
        )

        with self.assertRaises(ValidationError):
            confirm_order(
                order=order,
                tenant=self.tenant,
            )

    def test_cancel_pending_order_releases_inventory(self):
        inventory = Inventory.objects.get(
            product=self.product,
        )

        inventory.quantity = 100
        inventory.reserved_quantity = 2
        inventory.save()
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=self.product.price,
        )

        cancelled_order = cancel_order(
            order=order,
            tenant=self.tenant,
        )

        self.assertEqual(
            cancelled_order.status,
            Order.Status.CANCELLED,
        )

        inventory.refresh_from_db()

        self.assertEqual(
            inventory.quantity,
            100,
        )

        self.assertEqual(
            inventory.reserved_quantity,
            0,
        )


    def test_cannot_cancel_non_pending_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.CONFIRMED,
        )

        with self.assertRaises(ValidationError):
            cancel_order(
                order=order,
                tenant=self.tenant,
            )


    def test_cannot_cancel_order_from_another_tenant(self):
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        other_customer = Customer.objects.create(
            tenant=other_tenant,
            name="Other Customer",
        )

        order = Order.objects.create(
            tenant=other_tenant,
            customer=other_customer,
        )

        with self.assertRaises(ValidationError):
            cancel_order(
                order=order,
                tenant=self.tenant,
            )


    def test_cancel_order_does_not_change_inventory_when_validation_fails(self):
        inventory = Inventory.objects.get(
            product=self.product,
        )

        inventory.quantity = 100
        inventory.reserved_quantity = 2
        inventory.save()

        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.CONFIRMED,
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=self.product.price,
        )

        with self.assertRaises(ValidationError):
            cancel_order(
                order=order,
                tenant=self.tenant,
            )

        inventory.refresh_from_db()

        self.assertEqual(
            inventory.reserved_quantity,
            2,
        )

    def test_start_processing_confirmed_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.CONFIRMED,
        )

        processing_order = start_processing_order(
            order=order,
            tenant=self.tenant,
        )

        self.assertEqual(
            processing_order.status,
            Order.Status.PROCESSING,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PROCESSING,
        )

    def test_cannot_start_processing_pending_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PENDING,
        )

        with self.assertRaises(ValidationError):
            start_processing_order(
                order=order,
                tenant=self.tenant,
            )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PENDING,
        )

    def test_cannot_start_processing_non_confirmed_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.CANCELLED,
        )

        with self.assertRaises(ValidationError):
            start_processing_order(
                order=order,
                tenant=self.tenant,
            )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.CANCELLED,
        )

    def test_cannot_start_processing_order_from_another_tenant(self):
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        other_customer = Customer.objects.create(
            tenant=other_tenant,
            name="Other Customer",
        )

        order = Order.objects.create(
            tenant=other_tenant,
            customer=other_customer,
            status=Order.Status.CONFIRMED,
        )

        with self.assertRaises(ValidationError):
            start_processing_order(
                order=order,
                tenant=self.tenant,
            )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )

    def test_ship_processing_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PROCESSING,
        )

        shipped_order = ship_order(
            order=order,
            tenant=self.tenant,
        )

        self.assertEqual(
            shipped_order.status,
            Order.Status.SHIPPED,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.SHIPPED,
        )


    def test_cannot_ship_pending_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PENDING,
        )

        with self.assertRaises(ValidationError):
            ship_order(
                order=order,
                tenant=self.tenant,
            )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PENDING,
        )


    def test_cannot_ship_confirmed_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.CONFIRMED,
        )

        with self.assertRaises(ValidationError):
            ship_order(
                order=order,
                tenant=self.tenant,
            )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )


    def test_cannot_ship_order_from_another_tenant(self):
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        other_customer = Customer.objects.create(
            tenant=other_tenant,
            name="Other Customer",
        )

        order = Order.objects.create(
            tenant=other_tenant,
            customer=other_customer,
            status=Order.Status.PROCESSING,
        )

        with self.assertRaises(ValidationError):
            ship_order(
                order=order,
                tenant=self.tenant,
            )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PROCESSING,
        )

    def test_deliver_shipped_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.SHIPPED,
        )

        result = deliver_order(
            order=order,
            tenant=self.tenant,
        )

        self.assertEqual(
            result.status,
            Order.Status.DELIVERED,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.DELIVERED,
        )


    def test_cannot_deliver_pending_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PENDING,
        )

        with self.assertRaises(ValidationError):
            deliver_order(
                order=order,
                tenant=self.tenant,
            )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PENDING,
        )


    def test_cannot_deliver_processing_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PROCESSING,
        )

        with self.assertRaises(ValidationError):
            deliver_order(
                order=order,
                tenant=self.tenant,
            )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PROCESSING,
        )


    def test_cannot_deliver_order_from_another_tenant(self):
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        other_customer = Customer.objects.create(
            tenant=other_tenant,
            name="Other Customer",
        )

        order = Order.objects.create(
            tenant=other_tenant,
            customer=other_customer,
            status=Order.Status.SHIPPED,
        )

        with self.assertRaises(ValidationError):
            deliver_order(
                order=order,
                tenant=self.tenant,
            )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.SHIPPED,
        )