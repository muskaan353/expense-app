from django.conf import settings
from django.db import models

from apps.groups.models import Group


class ImportSession(models.Model):
    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        NEEDS_REVIEW = "needs_review", "Needs review"
        READY = "ready", "Ready"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        FAILED = "failed", "Failed"

    group = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="import_sessions",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="import_sessions",
    )
    source_file = models.FileField(upload_to="expense_imports/%Y/%m/%d/")
    original_filename = models.CharField(max_length=255)
    checksum_sha256 = models.CharField(max_length=64)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING,
    )
    row_count = models.PositiveIntegerField(default=0)
    issue_count = models.PositiveIntegerField(default=0)
    report = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("group", "checksum_sha256"),
                name="one_import_per_group_checksum",
            )
        ]

    def __str__(self):
        return self.original_filename


class ImportRow(models.Model):
    class Status(models.TextChoices):
        STAGED = "staged", "Staged"
        BLOCKED = "blocked", "Blocked"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    session = models.ForeignKey(
        ImportSession,
        on_delete=models.CASCADE,
        related_name="rows",
    )
    row_number = models.PositiveIntegerField()
    raw_data = models.JSONField()
    normalized_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.STAGED,
    )

    class Meta:
        ordering = ("row_number",)
        constraints = [
            models.UniqueConstraint(
                fields=("session", "row_number"),
                name="unique_import_row_number",
            )
        ]


class ImportIssue(models.Model):
    class Severity(models.TextChoices):
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved action"
        REJECTED = "rejected", "Rejected action"
        RESOLVED = "resolved", "Resolved"

    session = models.ForeignKey(
        ImportSession,
        on_delete=models.CASCADE,
        related_name="issues",
    )
    row = models.ForeignKey(
        ImportRow,
        on_delete=models.CASCADE,
        related_name="issues",
        null=True,
        blank=True,
    )
    row_number = models.PositiveIntegerField(null=True, blank=True)
    issue_code = models.CharField(max_length=60)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    field_name = models.CharField(max_length=120, blank=True)
    message = models.TextField()
    raw_value = models.TextField(blank=True)
    proposed_action = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("row_number", "id")
        indexes = [
            models.Index(fields=("session", "status", "severity")),
        ]

    def __str__(self):
        return f"{self.issue_code} at row {self.row_number}"
