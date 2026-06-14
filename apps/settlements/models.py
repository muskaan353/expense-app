from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.expenses.models import ExchangeRate
from apps.groups.models import Group, currency_validator


class Settlement(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="settlements",
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="settlements_paid",
    )
    payee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="settlements_received",
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    currency = models.CharField(max_length=3, validators=[currency_validator])
    base_amount = models.DecimalField(max_digits=14, decimal_places=2)
    exchange_rate = models.ForeignKey(
        ExchangeRate,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="settlements",
    )
    settled_at = models.DateTimeField()
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_settlements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-settled_at", "-id")
        indexes = [
            models.Index(fields=("group", "settled_at")),
        ]

    def __str__(self):
        return f"{self.payer} paid {self.payee} {self.base_amount}"
