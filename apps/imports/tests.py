from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.accounts.models import User
from apps.groups.services import create_group
from apps.imports.models import ImportSession
from apps.imports.services import stage_import


TEST_MEDIA_ROOT = Path(__file__).resolve().parents[2] / ".test-media"


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ImportServiceTests(TestCase):
    def test_import_stages_rows_and_surfaces_anomalies(self):
        owner = User.objects.create_user(
            email="owner@example.com",
            display_name="Owner",
            password="StrongPass!2048",
        )
        group = create_group(owner=owner, name="Flat")
        content = (
            b"description,amount,currency,date,paid_by,split_type\n"
            b"Dinner,100,INR,2026-03-01,Aisha,equal\n"
            b"Dinner,100,INR,2026-03-01,Aisha,equal\n"
            b"Refund,-20,INR,bad-date,Aisha,equal\n"
        )
        session = stage_import(
            group=group,
            uploaded_by=owner,
            uploaded_file=SimpleUploadedFile("expenses.csv", content),
        )

        self.assertEqual(session.row_count, 3)
        self.assertEqual(session.status, ImportSession.Status.NEEDS_REVIEW)
        self.assertTrue(session.issues.filter(issue_code="DUPLICATE_ROW").exists())
        self.assertTrue(
            session.issues.filter(issue_code="NON_POSITIVE_AMOUNT").exists()
        )
        self.assertTrue(session.issues.filter(issue_code="INVALID_DATE").exists())
