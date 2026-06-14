from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.expenses.services import _is_member_at
from apps.settlements.models import Settlement


@transaction.atomic
def create_settlement(*, created_by, **data):
    group = data["group"]
    payer = data["payer"]
    payee = data["payee"]
    settled_at = data["settled_at"]
    currency = data["currency"]
    exchange_rate = data.get("exchange_rate")

    for field, user in (("payer_id", payer), ("payee_id", payee)):
        if not _is_member_at(group=group, user=user, moment=settled_at):
            raise ValidationError({field: "User was not a member on this date."})

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
                {"exchange_rate_id": "Exchange rate currencies do not match."}
            )
        base_amount = (data["amount"] * exchange_rate.rate).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    return Settlement.objects.create(
        created_by=created_by,
        base_amount=base_amount,
        **data,
    )
