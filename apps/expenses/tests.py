from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.expenses.models import Expense
from apps.expenses.services import create_expense
from apps.groups.models import GroupMembership
from apps.groups.services import add_membership, create_group


class ExpenseServiceTests(APITestCase):
    def setUp(self):
        self.aisha = User.objects.create_user(
            email="aisha@example.com",
            display_name="Aisha",
            password="StrongPass!2048",
        )
        self.sam = User.objects.create_user(
            email="sam@example.com",
            display_name="Sam",
            password="StrongPass!2048",
        )
        self.group = create_group(owner=self.aisha, name="Flat", base_currency="INR")

    def test_equal_split_assigns_rounding_remainder_deterministically(self):
        moment = timezone.now()
        add_membership(
            group=self.group,
            user=self.sam,
            role=GroupMembership.Role.MEMBER,
            joined_at=moment,
        )
        expense = create_expense(
            created_by=self.aisha,
            group=self.group,
            paid_by=self.aisha,
            description="Internet",
            amount=Decimal("100.00"),
            currency="INR",
            split_type=Expense.SplitType.EQUAL,
            incurred_at=moment,
            splits=[{"user": self.aisha}, {"user": self.sam}],
        )
        self.assertEqual(
            list(expense.splits.values_list("base_amount", flat=True)),
            [Decimal("50.00"), Decimal("50.00")],
        )

    def test_person_cannot_be_split_before_they_joined(self):
        joined_at = timezone.now()
        add_membership(
            group=self.group,
            user=self.sam,
            role=GroupMembership.Role.MEMBER,
            joined_at=joined_at,
        )
        with self.assertRaisesMessage(ValidationError, "not a member"):
            create_expense(
                created_by=self.aisha,
                group=self.group,
                paid_by=self.aisha,
                description="March electricity",
                amount=Decimal("1000.00"),
                currency="INR",
                split_type=Expense.SplitType.EQUAL,
                incurred_at=joined_at - timedelta(days=10),
                splits=[{"user": self.aisha}, {"user": self.sam}],
            )

    def test_owner_membership_can_start_before_group_record_was_created(self):
        historical_date = timezone.now() - timedelta(days=120)
        group = create_group(
            owner=self.aisha,
            name="Historical flat",
            owner_joined_at=historical_date - timedelta(days=30),
        )
        expense = create_expense(
            created_by=self.aisha,
            group=group,
            paid_by=self.aisha,
            description="Old rent",
            amount=Decimal("5000.00"),
            currency="INR",
            split_type=Expense.SplitType.EQUAL,
            incurred_at=historical_date,
            splits=[{"user": self.aisha}],
        )
        self.assertEqual(expense.base_amount, Decimal("5000.00"))
