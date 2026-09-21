from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from customers.models import Customer
from orders.models import Order
from payments.models import Payment
from payments.services import create_payment
from tenants.models import Tenant


class PaymentServiceTestCase(TestCase):

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
        payment = create_payment(
            tenant=self.tenant,
            order=self.order,
            amount=Decimal("500.00"),
            method=Payment.Method.UPI,
        )

        self.assertEqual(
            payment.tenant,
            self.tenant,
        )

        self.assertEqual(
            payment.order,
            self.order,
        )

        self.assertEqual(
            payment.amount,
            Decimal("500.00"),
        )

        self.assertEqual(
            payment.method,
            Payment.Method.UPI,
        )

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

    def test_cannot_create_payment_for_other_tenant_order(self):
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

        with self.assertRaises(ValidationError):
            create_payment(
                tenant=self.tenant,
                order=other_order,
                amount=Decimal("500.00"),
                method=Payment.Method.UPI,
            )

    def test_payment_amount_must_be_greater_than_zero(self):
        with self.assertRaises(ValidationError):
            create_payment(
                tenant=self.tenant,
                order=self.order,
                amount=Decimal("0.00"),
                method=Payment.Method.CARD,
            )

    def test_payment_amount_must_match_order_total(self):
        with self.assertRaises(ValidationError):
            create_payment(
                tenant=self.tenant,
                order=self.order,
                amount=Decimal("400.00"),
                method=Payment.Method.CARD,
            )

    def test_cannot_create_duplicate_payment(self):
        create_payment(
            tenant=self.tenant,
            order=self.order,
            amount=Decimal("500.00"),
            method=Payment.Method.UPI,
        )

        with self.assertRaises(ValidationError):
            create_payment(
                tenant=self.tenant,
                order=self.order,
                amount=Decimal("500.00"),
                method=Payment.Method.CARD,
            )

    def test_payment_creation_is_atomic(self):
        with self.assertRaises(ValidationError):
            create_payment(
                tenant=self.tenant,
                order=self.order,
                amount=Decimal("400.00"),
                method=Payment.Method.UPI,
            )

        self.assertFalse(
            Payment.objects.filter(
                order=self.order,
            ).exists()
        )