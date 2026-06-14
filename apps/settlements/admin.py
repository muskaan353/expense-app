from django.contrib import admin

from apps.settlements.models import Settlement


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ("group", "payer", "payee", "base_amount", "settled_at")
    search_fields = ("group__name", "payer__email", "payee__email")
