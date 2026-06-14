from django.contrib import admin

from apps.expenses.models import ExchangeRate, Expense, ExpenseSplit


class ExpenseSplitInline(admin.TabularInline):
    model = ExpenseSplit
    extra = 0


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("description", "group", "paid_by", "base_amount", "incurred_at")
    list_filter = ("split_type", "status", "currency")
    search_fields = ("description", "group__name", "paid_by__email")
    inlines = (ExpenseSplitInline,)


admin.site.register(ExchangeRate)
