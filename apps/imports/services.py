import csv
import hashlib
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.imports.models import ImportIssue, ImportRow, ImportSession


COLUMN_ALIASES = {
    "description": {"description", "expense", "title", "item"},
    "amount": {"amount", "total", "cost"},
    "currency": {"currency", "currency_code"},
    "date": {"date", "expense_date", "incurred_at"},
    "paid_by": {"paid_by", "payer", "paid by"},
    "split_type": {"split_type", "split type", "split"},
}


def _checksum(uploaded_file):
    digest = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        digest.update(chunk)
    uploaded_file.seek(0)
    return digest.hexdigest()


def _canonical_headers(fieldnames):
    result = {}
    for fieldname in fieldnames or []:
        normalized = (fieldname or "").strip().casefold()
        for canonical, aliases in COLUMN_ALIASES.items():
            if normalized in aliases:
                result[canonical] = fieldname
    return result


@transaction.atomic
def stage_import(*, group, uploaded_by, uploaded_file):
    checksum = _checksum(uploaded_file)
    if ImportSession.objects.filter(
        group=group,
        checksum_sha256=checksum,
    ).exists():
        raise ValidationError({"file": "This exact file was already imported."})

    session = ImportSession.objects.create(
        group=group,
        uploaded_by=uploaded_by,
        source_file=uploaded_file,
        original_filename=uploaded_file.name,
        checksum_sha256=checksum,
    )
    try:
        _inspect_csv(session)
    except UnicodeDecodeError:
        _create_issue(
            session=session,
            code="INVALID_ENCODING",
            severity=ImportIssue.Severity.ERROR,
            message="The CSV is not valid UTF-8.",
            action="Upload a UTF-8 encoded CSV; no rows were applied.",
        )
        _finish_session(session)
    return session


def _inspect_csv(session):
    session.source_file.open("rb")
    text = io.TextIOWrapper(session.source_file.file, encoding="utf-8-sig", newline="")
    reader = csv.DictReader(text)
    headers = _canonical_headers(reader.fieldnames)
    missing = sorted(set(COLUMN_ALIASES) - set(headers))
    for column in missing:
        _create_issue(
            session=session,
            code="MISSING_REQUIRED_COLUMN",
            severity=ImportIssue.Severity.ERROR,
            field_name=column,
            message=f"No recognized '{column}' column was found.",
            action="Map the source column before approving this import.",
        )

    seen_rows = {}
    rows = []
    issues = []
    for row_number, raw in enumerate(reader, start=2):
        raw = {str(key): value for key, value in raw.items()}
        normalized = {
            canonical: (raw.get(source) or "").strip()
            for canonical, source in headers.items()
        }
        row = ImportRow(
            session=session,
            row_number=row_number,
            raw_data=raw,
            normalized_data=normalized,
        )
        rows.append(row)
        fingerprint = tuple(sorted(normalized.items()))
        if fingerprint in seen_rows:
            issues.append(
                _issue(
                    session,
                    row_number,
                    "DUPLICATE_ROW",
                    ImportIssue.Severity.WARNING,
                    f"Exact duplicate of row {seen_rows[fingerprint]}.",
                    "Keep staged until a reviewer approves skipping it.",
                )
            )
        else:
            seen_rows[fingerprint] = row_number
        issues.extend(_validate_row(session, row_number, normalized))

    ImportRow.objects.bulk_create(rows)
    rows_by_number = {
        row.row_number: row
        for row in ImportRow.objects.filter(session=session)
    }
    for issue in issues:
        issue.row = rows_by_number.get(issue.row_number)
    ImportIssue.objects.bulk_create(issues)
    blocked_numbers = {issue.row_number for issue in issues}
    ImportRow.objects.filter(
        session=session,
        row_number__in=blocked_numbers,
    ).update(status=ImportRow.Status.BLOCKED)
    _finish_session(session)


def _validate_row(session, row_number, normalized):
    issues = []
    amount = normalized.get("amount")
    if amount:
        try:
            parsed_amount = Decimal(amount.replace(",", ""))
            if parsed_amount <= 0:
                issues.append(
                    _issue(
                        session,
                        row_number,
                        "NON_POSITIVE_AMOUNT",
                        ImportIssue.Severity.WARNING,
                        "Amount is zero or negative.",
                        "Review whether this is a refund; do not import automatically.",
                        field_name="amount",
                        raw_value=amount,
                    )
                )
        except InvalidOperation:
            issues.append(
                _issue(
                    session,
                    row_number,
                    "INVALID_AMOUNT",
                    ImportIssue.Severity.ERROR,
                    "Amount is not a valid decimal.",
                    "Correct the amount before approval.",
                    field_name="amount",
                    raw_value=amount,
                )
            )

    currency = normalized.get("currency")
    if currency and (len(currency) != 3 or not currency.isalpha()):
        issues.append(
            _issue(
                session,
                row_number,
                "INVALID_CURRENCY",
                ImportIssue.Severity.ERROR,
                "Currency must be a three-letter code.",
                "Map it to a valid ISO 4217 code.",
                field_name="currency",
                raw_value=currency,
            )
        )

    date_value = normalized.get("date")
    if date_value and not _is_parseable_date(date_value):
        issues.append(
            _issue(
                session,
                row_number,
                "INVALID_DATE",
                ImportIssue.Severity.ERROR,
                "Date format was not recognized.",
                "Choose the intended date during review.",
                field_name="date",
                raw_value=date_value,
            )
        )
    return issues


def _is_parseable_date(value):
    formats = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S")
    return any(_try_date(value, date_format) for date_format in formats)


def _try_date(value, date_format):
    try:
        datetime.strptime(value, date_format)
        return True
    except ValueError:
        return False


def _issue(
    session,
    row_number,
    code,
    severity,
    message,
    action,
    field_name="",
    raw_value="",
):
    return ImportIssue(
        session=session,
        row_number=row_number,
        issue_code=code,
        severity=severity,
        field_name=field_name,
        message=message,
        raw_value=raw_value,
        proposed_action=action,
    )


def _create_issue(
    *,
    session,
    code,
    severity,
    message,
    action,
    field_name="",
):
    return ImportIssue.objects.create(
        session=session,
        issue_code=code,
        severity=severity,
        field_name=field_name,
        message=message,
        proposed_action=action,
    )


def _finish_session(session):
    issue_count = session.issues.count()
    row_count = session.rows.count()
    session.issue_count = issue_count
    session.row_count = row_count
    session.status = (
        ImportSession.Status.NEEDS_REVIEW
        if issue_count
        else ImportSession.Status.READY
    )
    session.completed_at = timezone.now()
    session.report = {
        "rows_staged": row_count,
        "issues_detected": issue_count,
        "issues_by_code": {
            code: session.issues.filter(issue_code=code).count()
            for code in session.issues.values_list("issue_code", flat=True).distinct()
        },
        "policy": "No staged row affects balances until explicit approval.",
    }
    session.save(
        update_fields=(
            "row_count",
            "issue_count",
            "status",
            "completed_at",
            "report",
        )
    )
