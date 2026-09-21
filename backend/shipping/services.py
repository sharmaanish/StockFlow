from django.core.exceptions import ValidationError
from django.db import transaction

from audit.services import create_audit_log
from shipping.models import Shipment


@transaction.atomic
def create_shipment(*, tenant, order, user=None):
    if order.tenant_id != tenant.id:
        raise ValidationError(
            "Order does not belong to this tenant."
        )

    if hasattr(order, "shipment"):
        raise ValidationError(
            "A shipment already exists for this order."
        )

    if order.status not in [
        "processing",
        "shipped",
    ]:
        raise ValidationError(
            "Shipment can only be created for a processing or shipped order."
        )

    shipment = Shipment.objects.create(
        tenant=tenant,
        order=order,
    )

    create_audit_log(
        tenant=tenant,
        user=user,
        action="SHIPMENT_CREATED",
        entity_type="Shipment",
        entity_id=shipment.id,
        metadata={
            "order_id": str(order.id),
            "status": shipment.status,
        },
    )

    return shipment


@transaction.atomic
def update_shipment_status(
    *,
    shipment,
    tenant,
    status,
    user=None,
):
    if shipment.tenant_id != tenant.id:
        raise ValidationError(
            "Shipment does not belong to this tenant."
        )

    allowed_transitions = {
        Shipment.Status.PENDING: [
            Shipment.Status.PROCESSING,
            Shipment.Status.CANCELLED,
        ],
        Shipment.Status.PROCESSING: [
            Shipment.Status.SHIPPED,
            Shipment.Status.CANCELLED,
        ],
        Shipment.Status.SHIPPED: [
            Shipment.Status.IN_TRANSIT,
        ],
        Shipment.Status.IN_TRANSIT: [
            Shipment.Status.DELIVERED,
        ],
        Shipment.Status.DELIVERED: [],
        Shipment.Status.CANCELLED: [],
    }

    if status not in allowed_transitions[shipment.status]:
        raise ValidationError(
            f"Cannot change shipment status from "
            f"{shipment.status} to {status}."
        )

    previous_status = shipment.status

    shipment.status = status
    shipment.save(
        update_fields=["status", "updated_at"]
    )

    create_audit_log(
        tenant=tenant,
        user=user,
        action="SHIPMENT_STATUS_CHANGED",
        entity_type="Shipment",
        entity_id=shipment.id,
        metadata={
            "previous_status": previous_status,
            "new_status": status,
            "order_id": str(shipment.order_id),
        },
    )

    return shipment