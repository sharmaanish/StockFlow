from decimal import Decimal

from rest_framework.test import APITestCase

from accounts.models import User
from customers.models import Customer
from orders.models import Order
from payments.models import Payment
from tenants.models import Tenant


class PaymentAPITestCase(APITestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
        )

        self.user = User.objects.create_user(
            tenant=self.tenant,
            email="payment-test@example.com",
            password="test-password",
        )

        self.customer = Customer.objects.create(
            tenant=self.tenant,
            name="Test Customer",
        )

        self.order = Order.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            total_amount=Decimal("500.00"),
        )

        self.client.force_authenticate(
            user=self.user,
        )

    def test_create_payment(self):
        response = self.client.post(
            "/api/v1/payments/",
            {
                "order": str(self.order.id),
                "amount": "500.00",
                "method": Payment.Method.UPI,
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
            response.data["amount"],
            "500.00",
        )

        self.assertEqual(
            response.data["status"],
            Payment.Status.PENDING,
        )

        self.assertEqual(
            response.data["method"],
            Payment.Method.UPI,
        )

        self.assertTrue(
            Payment.objects.filter(
                order=self.order,
            ).exists()
        )

    def test_create_payment_requires_authentication(self):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.post(
            "/api/v1/payments/",
            {
                "order": str(self.order.id),
                "amount": "500.00",
                "method": Payment.Method.UPI,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_create_payment_rejects_wrong_amount(self):
        response = self.client.post(
            "/api/v1/payments/",
            {
                "order": str(self.order.id),
                "amount": "400.00",
                "method": Payment.Method.UPI,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            Payment.objects.filter(
                order=self.order,
            ).exists()
        )

    def test_create_payment_rejects_other_tenant_order(self):
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
            total_amount=Decimal("500.00"),
        )

        response = self.client.post(
            "/api/v1/payments/",
            {
                "order": str(other_order.id),
                "amount": "500.00",
                "method": Payment.Method.UPI,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            Payment.objects.filter(
                order=other_order,
            ).exists()
        )

    def test_create_payment_rejects_duplicate_payment(self):
        Payment.objects.create(
            tenant=self.tenant,
            order=self.order,
            amount=Decimal("500.00"),
            method=Payment.Method.UPI,
        )

        response = self.client.post(
            "/api/v1/payments/",
            {
                "order": str(self.order.id),
                "amount": "500.00",
                "method": Payment.Method.CARD,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            Payment.objects.filter(
                order=self.order,
            ).count(),
            1,
        )

    def test_create_payment_rejects_invalid_method(self):
        response = self.client.post(
            "/api/v1/payments/",
            {
                "order": str(self.order.id),
                "amount": "500.00",
                "method": "bitcoin",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            Payment.objects.filter(
                order=self.order,
            ).exists()
        )