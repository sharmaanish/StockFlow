from django.core.exceptions import ValidationError
from django.db import transaction

from payments.models import Payment


@transaction.atomic
def create_payment(
    *,
    tenant,
    order,
    amount,
    method,
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

    return payment