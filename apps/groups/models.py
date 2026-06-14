from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


currency_validator = RegexValidator(
    regex=r"^[A-Z]{3}$",
    message="Currency must be a three-letter ISO 4217 code.",
)


class Group(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    base_currency = models.CharField(
        max_length=3,
        default="INR",
        validators=[currency_validator],
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_groups",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("owner", "archived_at")),
        ]

    def __str__(self):
        return self.name
