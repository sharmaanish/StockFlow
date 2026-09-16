from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "tenant",
        "price",
        "is_active",
    )

    list_filter = (
        "tenant",
        "is_active",
    )

    search_fields = (
        "sku",
        "name",
    )

    ordering = ("sku",)