from django.core.exceptions import ValidationError
from django.db import transaction

from audit.services import create_audit_log
from payments.models import Payment


@transaction.atomic
def create_payment(
    *,
    tenant,
    order,
    amount,
    method,
    user=None,
):
    if order.tenant_id != tenant.id:
        raise ValidationError(
            "Order does not belong to this tenant."
        )

    if amount <= 0:
        raise ValidationError(
            "Payment amount must be greater than zero."
        )

    if amount != order.total_amount:
        raise ValidationError(
            "Payment amount must match the order total."
        )

    if hasattr(order, "payment"):
        raise ValidationError(
            "A payment already exists for this order."
        )

    payment = Payment.objects.create(
        tenant=tenant,
        order=order,
        amount=amount,
        method=method,
    )

    create_audit_log(
        tenant=tenant,
        user=user,
        action="PAYMENT_CREATED",
        entity_type="Payment",
        entity_id=payment.id,
        metadata={
            "order_id": str(order.id),
            "amount": str(payment.amount),
            "method": payment.method,
            "status": payment.status,
        },
    )

    return payment