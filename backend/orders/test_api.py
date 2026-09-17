from decimal import Decimal

from rest_framework.test import APITestCase

from catalog.models import Product
from customers.models import Customer
from inventory.models import Inventory
from tenants.models import Tenant
from accounts.models import User
from orders.models import Order

class OrderAPITestCase(APITestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
        )

        self.user = User.objects.create_user(
            tenant=self.tenant,
            email="test@example.com",
            password="test-password",
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

        self.client.force_authenticate(user=self.user)

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
    
    def test_create_order_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.id),
                "items": [
                    {
                        "product": str(self.product.id),
                        "quantity": 1,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_create_order_rejects_empty_items(self):
        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.id),
                "items": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved_quantity,
            0,
        )

    def test_create_order_rejects_invalid_quantity(self):
        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.id),
                "items": [
                    {
                        "product": str(self.product.id),
                        "quantity": 0,
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

    def test_create_order_rejects_inactive_customer(self):
        self.customer.is_active = False
        self.customer.save(update_fields=["is_active"])

        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.id),
                "items": [
                    {
                        "product": str(self.product.id),
                        "quantity": 1,
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

    def test_create_order_rejects_inactive_product(self):
        self.product.is_active = False
        self.product.save(update_fields=["is_active"])

        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.id),
                "items": [
                    {
                        "product": str(self.product.id),
                        "quantity": 1,
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

    def test_create_order_rejects_customer_from_different_tenant(self):
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        other_customer = Customer.objects.create(
            tenant=other_tenant,
            name="Other Customer",
        )

        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(other_customer.id),
                "items": [
                    {
                        "product": str(self.product.id),
                        "quantity": 1,
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
        )

        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.id),
                "items": [
                    {
                        "product": str(other_product.id),
                        "quantity": 1,
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

    def test_create_order_rejects_missing_inventory(self):
        self.inventory.delete()

        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.id),
                "items": [
                    {
                        "product": str(self.product.id),
                        "quantity": 1,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_cancel_pending_order(self):
        create_response = self.client.post(
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

        self.assertEqual(create_response.status_code, 201)

        order_id = create_response.data["id"]

        self.inventory.refresh_from_db()
        self.assertEqual(
            self.inventory.reserved_quantity,
            2,
        )

        response = self.client.post(
            f"/api/v1/orders/{order_id}/cancel/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["status"],
            "cancelled",
        )

        self.inventory.refresh_from_db()
        self.assertEqual(
            self.inventory.reserved_quantity,
            0,
        )

        order = Order.objects.get(id=order_id)

        self.assertEqual(
            order.status,
            Order.Status.CANCELLED,
        )
    
    def test_cancel_order_requires_authentication(self):
        create_response = self.client.post(
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

        self.assertEqual(create_response.status_code, 201)

        order_id = create_response.data["id"]

        self.client.force_authenticate(user=None)

        response = self.client.post(
            f"/api/v1/orders/{order_id}/cancel/"
        )

        self.assertEqual(response.status_code, 401)

    def test_cancel_order_with_missing_order(self):
        missing_order_id = "00000000-0000-0000-0000-000000000000"

        response = self.client.post(
            f"/api/v1/orders/{missing_order_id}/cancel/"
        )

        self.assertEqual(response.status_code, 404)

    def test_cancel_non_pending_order(self):
        create_response = self.client.post(
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

        self.assertEqual(create_response.status_code, 201)

        order_id = create_response.data["id"]

        order = Order.objects.get(id=order_id)
        order.status = Order.Status.CONFIRMED
        order.save(update_fields=["status"])

        response = self.client.post(
            f"/api/v1/orders/{order_id}/cancel/"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "['Only pending orders can be cancelled.']",
        )

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved_quantity,
            2,
        )
    def test_cancel_order_from_different_tenant(self):
        create_response = self.client.post(
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

        self.assertEqual(create_response.status_code, 201)

        order_id = create_response.data["id"]

        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        other_user = User.objects.create_user(
            tenant=other_tenant,
            email="other@example.com",
            password="other-password",
        )

        self.client.force_authenticate(user=other_user)

        response = self.client.post(
            f"/api/v1/orders/{order_id}/cancel/"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "['Order does not belong to this tenant.']",
        )

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved_quantity,
            2,
        )

    def test_confirm_pending_order(self):
        create_response = self.client.post(
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

        self.assertEqual(create_response.status_code, 201)

        order_id = create_response.data["id"]

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved_quantity,
            2,
        )

        response = self.client.post(
            f"/api/v1/orders/{order_id}/confirm/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["status"],
            "confirmed",
        )

        order = Order.objects.get(id=order_id)

        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved_quantity,
            2,
        )

    def test_confirm_order_requires_authentication(self):
        create_response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.id),
                "items": [
                    {
                        "product": str(self.product.id),
                        "quantity": 1,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, 201)

        order_id = create_response.data["id"]

        self.client.force_authenticate(user=None)

        response = self.client.post(
            f"/api/v1/orders/{order_id}/confirm/"
        )

        self.assertEqual(response.status_code, 401)

    def test_confirm_order_with_missing_order(self):
        missing_order_id = "00000000-0000-0000-0000-000000000000"

        response = self.client.post(
            f"/api/v1/orders/{missing_order_id}/confirm/"
        )

        self.assertEqual(response.status_code, 404)

    def test_confirm_non_pending_order(self):
        create_response = self.client.post(
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

        self.assertEqual(create_response.status_code, 201)

        order_id = create_response.data["id"]

        order = Order.objects.get(id=order_id)

        order.status = Order.Status.CANCELLED

        order.save(
            update_fields=["status"]
        )

        response = self.client.post(
            f"/api/v1/orders/{order_id}/confirm/"
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data["detail"],
            "['Only pending orders can be confirmed.']",
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.CANCELLED,
        )

    def test_confirm_order_from_different_tenant(self):
        create_response = self.client.post(
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

        self.assertEqual(create_response.status_code, 201)

        order_id = create_response.data["id"]

        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        other_user = User.objects.create_user(
            tenant=other_tenant,
            email="other@example.com",
            password="other-password",
        )

        self.client.force_authenticate(user=other_user)

        response = self.client.post(
            f"/api/v1/orders/{order_id}/confirm/"
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data["detail"],
            "['Order does not belong to this tenant.']",
        )

        order = Order.objects.get(id=order_id)

        self.assertEqual(
            order.status,
            Order.Status.PENDING,
        )

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved_quantity,
            2,
        )