from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q


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


class GroupMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="group_memberships",
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField()
    left_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("joined_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=Q(left_at__isnull=True) | Q(left_at__gt=models.F("joined_at")),
                name="membership_left_after_joined",
            ),
            models.UniqueConstraint(
                fields=("group", "user"),
                condition=Q(left_at__isnull=True),
                name="one_open_membership_per_group_user",
            ),
        ]
        indexes = [
            models.Index(fields=("group", "user", "joined_at", "left_at")),
        ]

    def clean(self):
        if self.left_at and self.left_at <= self.joined_at:
            raise ValidationError({"left_at": "left_at must be after joined_at."})

    def is_active_at(self, moment):
        return self.joined_at <= moment and (
            self.left_at is None or moment < self.left_at
        )

    def __str__(self):
        return f"{self.user} in {self.group}"
