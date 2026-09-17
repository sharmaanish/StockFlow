from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.models import Inventory
from .models import Order, OrderItem


@transaction.atomic
def create_order(
    *,
    tenant,
    customer,
    items,
):
    if not items:
        raise ValidationError(
            "Order must contain at least one item."
        )

    if customer.tenant_id != tenant.id:
        raise ValidationError(
            "Customer does not belong to this tenant."
        )

    if not customer.is_active:
        raise ValidationError(
            "Customer is inactive."
        )

    inventories = {}
    product_ids = set()

    for item in items:
        quantity = item["quantity"]

        if quantity <= 0:
            raise ValidationError(
                "Item quantity must be greater than zero."
            )

        product = item["product"]

        if product.id in product_ids:
            raise ValidationError(
                f"Product {product.sku} appears more than once in the order."
            )

        product_ids.add(product.id)

        if product.tenant_id != tenant.id:
            raise ValidationError(
                f"Product {product.sku} does not belong to this tenant."
            )

        if not product.is_active:
            raise ValidationError(
                f"Product {product.sku} is inactive."
            )

        inventory = (
            Inventory.objects
            .select_for_update()
            .filter(product=product)
            .first()
        )

        if inventory is None:
            raise ValidationError(
                f"No inventory record exists for product {product.sku}."
            )

        available_quantity = (
            inventory.quantity - inventory.reserved_quantity
        )

        if quantity > available_quantity:
            raise ValidationError(
                f"Insufficient inventory for product {product.sku}."
            )

        inventories[product.id] = inventory

    order = Order.objects.create(
        tenant=tenant,
        customer=customer,
    )

    total_amount = Decimal("0")

    for item in items:
        product = item["product"]
        quantity = item["quantity"]

        unit_price = product.price

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
        )

        inventory = inventories[product.id]

        inventory.reserved_quantity += quantity
        inventory.save(
            update_fields=["reserved_quantity", "updated_at"]
        )

        total_amount += quantity * unit_price

    order.total_amount = total_amount
    order.save(
        update_fields=["total_amount", "updated_at"]
    )

    return order

@transaction.atomic
def confirm_order(*, order, tenant):
    if order.tenant_id != tenant.id:
        raise ValidationError(
            "Order does not belong to this tenant."
        )

    if order.status != Order.Status.PENDING:
        raise ValidationError(
            "Only pending orders can be confirmed."
        )

    order.status = Order.Status.CONFIRMED
    order.save(
        update_fields=["status", "updated_at"]
    )

    return order

@transaction.atomic
def cancel_order(*, order, tenant):
    if order.tenant_id != tenant.id:
        raise ValidationError(
            "Order does not belong to this tenant."
        )

    if order.status != Order.Status.PENDING:
        raise ValidationError(
            "Only pending orders can be cancelled."
        )

    for item in order.items.all():
        inventory = (
            Inventory.objects
            .select_for_update()
            .get(product=item.product)
        )

        inventory.reserved_quantity -= item.quantity
        inventory.save(
            update_fields=["reserved_quantity", "updated_at"]
        )

    order.status = Order.Status.CANCELLED
    order.save(
        update_fields=["status", "updated_at"]
    )

    return order