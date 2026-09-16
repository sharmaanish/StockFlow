from django.contrib import admin

from .models import Inventory


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "quantity",
        "reserved_quantity",
        "available_quantity",
        "updated_at",
    )

    search_fields = (
        "product__sku",
        "product__name",
    )

    ordering = ("product__sku",)

    @admin.display(description="Available")
    def available_quantity(self, obj):
        return obj.quantity - obj.reserved_quantity
