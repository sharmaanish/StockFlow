from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "phone",
        "tenant",
        "is_active",
        "created_at",
    )

    list_filter = (
        "tenant",
        "is_active",
    )

    search_fields = (
        "name",
        "email",
        "phone",
    )

    ordering = ("name",)
