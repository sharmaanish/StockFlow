from decimal import Decimal

from rest_framework.test import APITestCase

from catalog.models import Product
from customers.models import Customer
from inventory.models import Inventory
from tenants.models import Tenant
from accounts.models import User
from orders.models import Order, OrderItem


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

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved_quantity,
            2,
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

    def test_ship_processing_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PROCESSING,
        )

        response = self.client.post(
            f"/api/v1/orders/{order.id}/ship/",
        )

        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.SHIPPED,
        )

    def test_ship_order_requires_authentication(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PROCESSING,
        )

        self.client.force_authenticate(user=None)

        response = self.client.post(
            f"/api/v1/orders/{order.id}/ship/",
        )

        self.assertEqual(response.status_code, 401)

    def test_ship_missing_order(self):
        response = self.client.post(
            "/api/v1/orders/00000000-0000-0000-0000-000000000000/ship/",
        )

        self.assertEqual(response.status_code, 404)

    def test_ship_non_processing_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PENDING,
        )

        response = self.client.post(
            f"/api/v1/orders/{order.id}/ship/",
        )

        self.assertEqual(response.status_code, 400)

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PENDING,
        )

    def test_ship_order_from_different_tenant(self):
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

        response = self.client.post(
            f"/api/v1/orders/{order.id}/ship/",
        )

        self.assertEqual(response.status_code, 400)

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

        response = self.client.post(
            f"/api/v1/orders/{order.id}/deliver/",
        )

        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.DELIVERED,
        )

    def test_deliver_order_requires_authentication(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.SHIPPED,
        )

        self.client.force_authenticate(user=None)

        response = self.client.post(
            f"/api/v1/orders/{order.id}/deliver/",
        )

        self.assertEqual(response.status_code, 401)

    def test_deliver_missing_order(self):
        response = self.client.post(
            "/api/v1/orders/00000000-0000-0000-0000-000000000000/deliver/",
        )

        self.assertEqual(response.status_code, 404)

    def test_deliver_non_shipped_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PROCESSING,
        )

        response = self.client.post(
            f"/api/v1/orders/{order.id}/deliver/",
        )

        self.assertEqual(response.status_code, 400)

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PROCESSING,
        )

    def test_deliver_order_from_different_tenant(self):
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

        response = self.client.post(
            f"/api/v1/orders/{order.id}/deliver/",
        )

        self.assertEqual(response.status_code, 400)

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.SHIPPED,
        )

    def test_retrieve_order(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PROCESSING,
            total_amount=Decimal("500.00"),
        )

        product = Product.objects.create(
            tenant=self.tenant,
            sku="TEST-002",
            name="Test Product 2",
            price=Decimal("250.00"),
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=2,
            unit_price=Decimal("250.00"),
        )

        response = self.client.get(
            f"/api/v1/orders/{order.id}/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["id"],
            str(order.id),
        )
        self.assertEqual(
            response.data["status"],
            Order.Status.PROCESSING,
        )
        self.assertEqual(
            response.data["total_amount"],
            "500.00",
        )

        self.assertEqual(
            len(response.data["items"]),
            1,
        )

        self.assertEqual(
            response.data["items"][0]["product"],
            str(product.id),
        )

        self.assertEqual(
            response.data["items"][0]["quantity"],
            2,
        )

        self.assertEqual(
            response.data["items"][0]["unit_price"],
            "250.00",
        )

    def test_retrieve_order_requires_authentication(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
        )

        self.client.force_authenticate(user=None)

        response = self.client.get(
            f"/api/v1/orders/{order.id}/",
        )

        self.assertEqual(response.status_code, 401)

    def test_retrieve_missing_order(self):
        response = self.client.get(
            "/api/v1/orders/00000000-0000-0000-0000-000000000000/",
        )

        self.assertEqual(response.status_code, 404)

    def test_cannot_retrieve_order_from_different_tenant(self):
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

        response = self.client.get(
            f"/api/v1/orders/{order.id}/",
        )

        self.assertEqual(response.status_code, 404)

    def test_retrieve_order_without_items(self):
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            total_amount=0,
        )

        response = self.client.get(
            f"/api/v1/orders/{order.id}/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["id"],
            str(order.id),
        )
        self.assertEqual(
            response.data["items"],
            [],
        )

    def test_list_orders(self):
        order_1 = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PENDING,
            total_amount=Decimal("100.00"),
        )

        order_2 = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.CONFIRMED,
            total_amount=Decimal("200.00"),
        )

        response = self.client.get(
            "/api/v1/orders/",
        )

        self.assertEqual(response.status_code, 200)

        # Pagination returns the orders inside the "results" key.
        self.assertEqual(
            len(response.data["results"]),
            2,
        )

        returned_ids = {
            order["id"]
            for order in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(order_1.id),
                str(order_2.id),
            },
        )

    def test_list_orders_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            "/api/v1/orders/",
        )

        self.assertEqual(response.status_code, 401)

    def test_list_orders_only_returns_current_tenant_orders(self):
        tenant_2 = Tenant.objects.create(
            name="Second Tenant",
            slug="second-tenant",
        )

        customer_2 = Customer.objects.create(
            tenant=tenant_2,
            name="Second Customer",
            email="second@example.com",
        )

        tenant_1_order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            total_amount=Decimal("100.00"),
        )

        tenant_2_order = Order.objects.create(
            tenant=tenant_2,
            customer=customer_2,
            total_amount=Decimal("200.00"),
        )

        response = self.client.get(
            "/api/v1/orders/",
        )

        self.assertEqual(response.status_code, 200)

        # Pagination returns the orders inside the "results" key.
        returned_ids = {
            order["id"]
            for order in response.data["results"]
        }

        self.assertIn(
            str(tenant_1_order.id),
            returned_ids,
        )

        self.assertNotIn(
            str(tenant_2_order.id),
            returned_ids,
        )

    def test_list_orders_returns_empty_list_when_no_orders_exist(self):
        response = self.client.get(
            "/api/v1/orders/",
        )

        self.assertEqual(response.status_code, 200)

        # An empty paginated response contains an empty "results" list.
        self.assertEqual(
            response.data["results"],
            [],
        )

    def test_search_orders_by_order_id(self):
        # Create an order that we will search for.
        # response = self.client.get(
        #     "/api/v1/orders/",
        #     {"search": "Unique Search Customer"},
        # )
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PENDING,
            total_amount=Decimal("100.00"),
        )

        response = self.client.get(
            f"/api/v1/orders/?search={order.id}",
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["id"],
            str(order.id),
        )


    def test_search_orders_by_customer_id(self):
        # Create an order belonging to our test customer.
        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            total_amount=Decimal("100.00"),
        )

        response = self.client.get(
            f"/api/v1/orders/?search={self.customer.id}",
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["id"],
            str(order.id),
        )


    def test_search_orders_by_customer_name(self):
        # Use a distinctive customer name for the search.
        self.customer.name = "Unique Search Customer"
        self.customer.save(update_fields=["name"])

        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            total_amount=Decimal("100.00"),
        )

        response = self.client.get(
            "/api/v1/orders/?search=Unique%20Search%20Customer",
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["id"],
            str(order.id),
        )


    def test_search_orders_by_customer_email(self):
        # Give the customer a searchable email address.
        self.customer.email = "unique-search@example.com"
        self.customer.save(update_fields=["email"])

        order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            total_amount=Decimal("100.00"),
        )

        response = self.client.get(
            "/api/v1/orders/?search=unique-search@example.com",
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["id"],
            str(order.id),
        )


    def test_search_orders_with_status_filter(self):
        # Create one pending order and one confirmed order.
        pending_order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.PENDING,
            total_amount=Decimal("100.00"),
        )

        confirmed_order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            status=Order.Status.CONFIRMED,
            total_amount=Decimal("200.00"),
        )

        response = self.client.get(
            f"/api/v1/orders/?search={self.customer.id}"
            f"&status={Order.Status.CONFIRMED}",
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["id"],
            str(confirmed_order.id),
        )

        self.assertNotEqual(
            results[0]["id"],
            str(pending_order.id),
        )


    def test_search_orders_respects_tenant_isolation(self):
        # Create an order in the current tenant.
        current_tenant_order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            total_amount=Decimal("100.00"),
        )

        # Create another tenant and customer.
        other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        other_customer = Customer.objects.create(
            tenant=other_tenant,
            name=self.customer.name,
            email=self.customer.email,
        )

        # Create an order for the other tenant.
        other_tenant_order = Order.objects.create(
            tenant=other_tenant,
            customer=other_customer,
            total_amount=Decimal("200.00"),
        )

        # Search using the shared customer name.
        response = self.client.get(
            f"/api/v1/orders/?search={self.customer.name}",
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        returned_ids = {
            order["id"]
            for order in results
        }

        # Our tenant's order must be visible.
        self.assertIn(
            str(current_tenant_order.id),
            returned_ids,
        )

        # The other tenant's order must NOT be visible.
        self.assertNotIn(
            str(other_tenant_order.id),
            returned_ids,
        )


    def test_search_orders_returns_empty_for_no_match(self):
        # Create an order that should not match the search.
        Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            total_amount=Decimal("100.00"),
        )

        response = self.client.get(
            "/api/v1/orders/?search=does-not-exist",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["results"],
            [],
        )

    def test_ordering_orders_by_created_at_ascending(self):
        response = self.client.get(
            "/api/v1/orders/",
            {"ordering": "created_at"},
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        created_dates = [
            order["created_at"]
            for order in results
        ]

        self.assertEqual(
            created_dates,
            sorted(created_dates),
        )


    def test_ordering_orders_by_created_at_descending(self):
        response = self.client.get(
            "/api/v1/orders/",
            {"ordering": "-created_at"},
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        created_dates = [
            order["created_at"]
            for order in results
        ]

        self.assertEqual(
            created_dates,
            sorted(
                created_dates,
                reverse=True,
            ),
        )


    def test_ordering_orders_by_total_amount_ascending(self):
        response = self.client.get(
            "/api/v1/orders/",
            {"ordering": "total_amount"},
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        total_amounts = [
            order["total_amount"]
            for order in results
        ]

        self.assertEqual(
            total_amounts,
            sorted(total_amounts),
        )


    def test_ordering_orders_by_total_amount_descending(self):
        response = self.client.get(
            "/api/v1/orders/",
            {"ordering": "-total_amount"},
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        total_amounts = [
            order["total_amount"]
            for order in results
        ]

        self.assertEqual(
            total_amounts,
            sorted(
                total_amounts,
                reverse=True,
            ),
        )


    def test_ordering_rejects_invalid_field(self):
        response = self.client.get(
            "/api/v1/orders/",
            {"ordering": "customer"},
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "Invalid ordering field",
            response.data["detail"],
        )


    def test_ordering_works_with_status_filter(self):
        response = self.client.get(
            "/api/v1/orders/",
            {
                "status": "pending",
                "ordering": "-created_at",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        created_dates = [
            order["created_at"]
            for order in results
        ]

        self.assertEqual(
            created_dates,
            sorted(
                created_dates,
                reverse=True,
            ),
        )

        for order in results:
            self.assertEqual(
                order["status"],
                "pending",
            )

            