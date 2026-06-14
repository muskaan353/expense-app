from collections import defaultdict
from decimal import Decimal

from apps.expenses.models import Expense
from apps.settlements.models import Settlement


def calculate_group_balances(*, group):
    balances = defaultdict(lambda: Decimal("0.00"))
    entries = defaultdict(list)
    names = {}

    expenses = (
        Expense.objects.filter(group=group, status=Expense.Status.ACTIVE)
        .select_related("paid_by")
        .prefetch_related("splits__user")
    )
    for expense in expenses:
        names[expense.paid_by_id] = expense.paid_by.display_name
        balances[expense.paid_by_id] += expense.base_amount
        entries[expense.paid_by_id].append(
            {
                "kind": "expense_paid",
                "reference_id": expense.id,
                "description": expense.description,
                "amount": expense.base_amount,
            }
        )
        for split in expense.splits.all():
            names[split.user_id] = split.user.display_name
            balances[split.user_id] -= split.base_amount
            entries[split.user_id].append(
                {
                    "kind": "expense_share",
                    "reference_id": expense.id,
                    "description": expense.description,
                    "amount": -split.base_amount,
                }
            )

    settlements = Settlement.objects.filter(group=group).select_related("payer", "payee")
    for settlement in settlements:
        names[settlement.payer_id] = settlement.payer.display_name
        names[settlement.payee_id] = settlement.payee.display_name
        balances[settlement.payer_id] += settlement.base_amount
        balances[settlement.payee_id] -= settlement.base_amount
        entries[settlement.payer_id].append(
            {
                "kind": "settlement_sent",
                "reference_id": settlement.id,
                "description": f"Payment to {settlement.payee.display_name}",
                "amount": settlement.base_amount,
            }
        )
        entries[settlement.payee_id].append(
            {
                "kind": "settlement_received",
                "reference_id": settlement.id,
                "description": f"Payment from {settlement.payer.display_name}",
                "amount": -settlement.base_amount,
            }
        )

    members = [
        {
            "user_id": user_id,
            "display_name": names[user_id],
            "balance": balance,
            "entries": entries[user_id],
        }
        for user_id, balance in sorted(balances.items())
    ]
    return {
        "group_id": group.id,
        "currency": group.base_currency,
        "members": members,
        "suggested_settlements": _simplify_debts(balances),
    }


def _simplify_debts(balances):
    debtors = [
        [user_id, -amount]
        for user_id, amount in balances.items()
        if amount < Decimal("0.00")
    ]
    creditors = [
        [user_id, amount]
        for user_id, amount in balances.items()
        if amount > Decimal("0.00")
    ]
    debtors.sort(key=lambda item: item[0])
    creditors.sort(key=lambda item: item[0])
    result = []
    debtor_index = creditor_index = 0

    while debtor_index < len(debtors) and creditor_index < len(creditors):
        debtor_id, debt = debtors[debtor_index]
        creditor_id, credit = creditors[creditor_index]
        amount = min(debt, credit)
        result.append(
            {"payer_id": debtor_id, "payee_id": creditor_id, "amount": amount}
        )
        debtors[debtor_index][1] -= amount
        creditors[creditor_index][1] -= amount
        if debtors[debtor_index][1] == 0:
            debtor_index += 1
        if creditors[creditor_index][1] == 0:
            creditor_index += 1
    return result
