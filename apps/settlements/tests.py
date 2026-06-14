from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.balances.services import calculate_group_balances
from apps.expenses.models import Expense
from apps.expenses.services import create_expense
from apps.groups.models import GroupMembership
from apps.groups.services import add_membership, create_group
from apps.settlements.services import create_settlement


class SettlementAndBalanceTests(APITestCase):
    def test_settlement_reduces_suggested_debt_and_keeps_breakdown(self):
        aisha = User.objects.create_user(
            email="aisha@example.com",
            display_name="Aisha",
            password="StrongPass!2048",
        )
        rohan = User.objects.create_user(
            email="rohan@example.com",
            display_name="Rohan",
            password="StrongPass!2048",
        )
        group = create_group(owner=aisha, name="Flat")
        moment = timezone.now()
        add_membership(
            group=group,
            user=rohan,
            role=GroupMembership.Role.MEMBER,
            joined_at=moment,
        )
        create_expense(
            created_by=aisha,
            group=group,
            paid_by=aisha,
            description="Dinner",
            amount=Decimal("100.00"),
            currency="INR",
            split_type=Expense.SplitType.EQUAL,
            incurred_at=moment,
            splits=[{"user": aisha}, {"user": rohan}],
        )
        create_settlement(
            created_by=rohan,
            group=group,
            payer=rohan,
            payee=aisha,
            amount=Decimal("20.00"),
            currency="INR",
            settled_at=moment,
        )

        result = calculate_group_balances(group=group)
        self.assertEqual(
            result["suggested_settlements"],
            [{"payer_id": rohan.id, "payee_id": aisha.id, "amount": Decimal("30.00")}],
        )
        rohan_balance = next(
            item for item in result["members"] if item["user_id"] == rohan.id
        )
        self.assertEqual(len(rohan_balance["entries"]), 2)
