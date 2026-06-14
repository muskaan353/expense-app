from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.ai_assistant.services import answer_balance_question
from apps.expenses.models import Expense
from apps.expenses.services import create_expense
from apps.groups.services import create_group


class AssistantServiceTests(APITestCase):
    def test_explanation_cites_underlying_expense(self):
        user = User.objects.create_user(
            email="aisha@example.com",
            display_name="Aisha",
            password="StrongPass!2048",
        )
        group = create_group(owner=user, name="Flat")
        expense = create_expense(
            created_by=user,
            group=group,
            paid_by=user,
            description="Internet",
            amount=Decimal("100.00"),
            currency="INR",
            split_type=Expense.SplitType.EQUAL,
            incurred_at=timezone.now(),
            splits=[{"user": user}],
        )

        result = answer_balance_question(
            group=group,
            user=user,
            question="Why is my balance this amount?",
        )
        self.assertEqual(result["generated_from"], "deterministic_ledger")
        self.assertIn(
            {"kind": "expense_paid", "reference_id": expense.id},
            result["citations"],
        )
