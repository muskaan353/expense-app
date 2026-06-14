from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.expenses.models import Expense, ExpenseSplit
from apps.groups.models import GroupMembership
from apps.groups.selectors import accessible_groups_for


CENT = Decimal("0.01")


def _is_member_at(*, group, user, moment):
    return GroupMembership.objects.filter(
        group=group,
        user=user,
        joined_at__lte=moment,
    ).filter(left_at__isnull=True).exists() or GroupMembership.objects.filter(
        group=group,
        user=user,
        joined_at__lte=moment,
        left_at__gt=moment,
    ).exists()


def _allocate_splits(*, split_type, base_amount, splits):
    if not splits:
        raise ValidationError({"splits": "At least one split is required."})
    users = [item["user"] for item in splits]
    if len(set(user.pk for user in users)) != len(users):
        raise ValidationError({"splits": "Each user can appear only once."})

    if split_type == Expense.SplitType.EQUAL:
        raw_weights = [Decimal("1")] * len(splits)
    else:
        if any(item.get("value") is None for item in splits):
            raise ValidationError({"splits": "Every split requires a value."})
        raw_weights = [item["value"] for item in splits]

    if any(value < 0 for value in raw_weights):
        raise ValidationError({"splits": "Split values cannot be negative."})

    if split_type == Expense.SplitType.EXACT:
        allocated = [value.quantize(CENT, rounding=ROUND_HALF_UP) for value in raw_weights]
        if sum(allocated) != base_amount:
            raise ValidationError(
                {"splits": "Exact split amounts must equal the base amount."}
            )
        return allocated

    if split_type == Expense.SplitType.PERCENTAGE:
        if sum(raw_weights) != Decimal("100"):
            raise ValidationError({"splits": "Percentages must total 100."})
        weights = [value / Decimal("100") for value in raw_weights]
    else:
        total_weight = sum(raw_weights)
        if total_weight <= 0:
            raise ValidationError({"splits": "Split weights must total above zero."})
        weights = [value / total_weight for value in raw_weights]

    allocated = [
        (base_amount * weight).quantize(CENT, rounding=ROUND_HALF_UP)
        for weight in weights
    ]
    allocated[-1] += base_amount - sum(allocated)
    return allocated


@transaction.atomic
def create_expense(*, created_by, splits, **data):
    group = data["group"]
    paid_by = data["paid_by"]
    incurred_at = data["incurred_at"]
    currency = data["currency"]
    exchange_rate = data.get("exchange_rate")

    if not accessible_groups_for(user=created_by).filter(pk=group.pk).exists():
        raise PermissionDenied("You do not have access to this group.")
    if not _is_member_at(group=group, user=paid_by, moment=incurred_at):
        raise ValidationError({"paid_by_id": "Payer was not a member on this date."})
    for split in splits:
        if not _is_member_at(group=group, user=split["user"], moment=incurred_at):
            raise ValidationError(
                {"splits": f"{split['user'].email} was not a member on this date."}
            )

    if currency == group.base_currency:
        if exchange_rate is not None:
            raise ValidationError(
                {"exchange_rate_id": "No exchange rate is needed for base currency."}
            )
        base_amount = data["amount"]
    else:
        if exchange_rate is None:
            raise ValidationError(
                {"exchange_rate_id": "An exchange rate is required."}
            )
        if (
            exchange_rate.source_currency != currency
            or exchange_rate.target_currency != group.base_currency
        ):
            raise ValidationError(
                {"exchange_rate_id": "Exchange rate currencies do not match the expense."}
            )
        base_amount = (data["amount"] * exchange_rate.rate).quantize(
            CENT,
            rounding=ROUND_HALF_UP,
        )

    allocations = _allocate_splits(
        split_type=data["split_type"],
        base_amount=base_amount,
        splits=splits,
    )
    expense = Expense.objects.create(
        created_by=created_by,
        base_amount=base_amount,
        **data,
    )
    ExpenseSplit.objects.bulk_create(
        [
            ExpenseSplit(
                expense=expense,
                user=item["user"],
                base_amount=allocation,
                input_value=item.get("value"),
            )
            for item, allocation in zip(splits, allocations, strict=True)
        ]
    )
    return expense
