from decimal import Decimal

from django.test import TestCase

from orders.models import Order
from payments.models import Payment
from tenants.models import Tenant
from customers.models import Customer


class PaymentModelTestCase(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
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

    def test_create_payment(self):
        payment = Payment.objects.create(
            tenant=self.tenant,
            order=self.order,
            amount=Decimal("500.00"),
            method=Payment.Method.UPI,
        )

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

        self.assertEqual(
            payment.amount,
            Decimal("500.00"),
        )

        self.assertEqual(
            payment.method,
            Payment.Method.UPI,
        )

    def test_payment_str_returns_id(self):
        payment = Payment.objects.create(
            tenant=self.tenant,
            order=self.order,
            amount=Decimal("500.00"),
            method=Payment.Method.CARD,
        )

        self.assertEqual(
            str(payment),
            str(payment.id),
        )

    def test_payment_has_one_order(self):
        payment = Payment.objects.create(
            tenant=self.tenant,
            order=self.order,
            amount=Decimal("500.00"),
            method=Payment.Method.CASH,
        )

        self.assertEqual(
            payment.order,
            self.order,
        )