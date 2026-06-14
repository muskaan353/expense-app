from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.groups.models import Group, currency_validator


class ExchangeRate(models.Model):
    source_currency = models.CharField(max_length=3, validators=[currency_validator])
    target_currency = models.CharField(max_length=3, validators=[currency_validator])
    rate = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        validators=[MinValueValidator(Decimal("0.00000001"))],
    )
    effective_date = models.DateField()
    source = models.CharField(max_length=120, default="manual")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-effective_date", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("source_currency", "target_currency", "effective_date", "source"),
                name="unique_exchange_rate_source_day",
            )
        ]

    def __str__(self):
        return (
            f"1 {self.source_currency} = {self.rate} "
            f"{self.target_currency} on {self.effective_date}"
        )


class Expense(models.Model):
    class SplitType(models.TextChoices):
        EQUAL = "equal", "Equal"
        EXACT = "exact", "Exact amounts"
        PERCENTAGE = "percentage", "Percentage"
        SHARES = "shares", "Shares"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        VOID = "void", "Void"

    group = models.ForeignKey(Group, on_delete=models.PROTECT, related_name="expenses")
    description = models.CharField(max_length=255)
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    currency = models.CharField(max_length=3, validators=[currency_validator])
    base_amount = models.DecimalField(max_digits=14, decimal_places=2)
    exchange_rate = models.ForeignKey(
        ExchangeRate,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="expenses",
    )
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="paid_expenses",
    )
    split_type = models.CharField(max_length=12, choices=SplitType.choices)
    incurred_at = models.DateTimeField()
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_expenses",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-incurred_at", "-id")
        indexes = [
            models.Index(fields=("group", "status", "incurred_at")),
        ]

    def __str__(self):
        return self.description


class ExpenseSplit(models.Model):
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name="splits",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="expense_splits",
    )
    base_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    input_value = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Exact amount, percentage, or share count supplied by the user.",
    )

    class Meta:
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(
                fields=("expense", "user"),
                name="one_split_per_expense_user",
            )
        ]

    def __str__(self):
        return f"{self.user}: {self.base_amount}"
