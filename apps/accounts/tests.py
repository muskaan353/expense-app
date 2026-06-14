from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User


class AuthenticationApiTests(APITestCase):
    def test_register_login_and_read_profile(self):
        register_response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "aisha@example.com",
                "display_name": "Aisha",
                "password": "StrongPass!2048",
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="aisha@example.com").exists())

        login_response = self.client.post(
            reverse("accounts:login"),
            {"email": "aisha@example.com", "password": "StrongPass!2048"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}"
        )

        profile_response = self.client.get(reverse("accounts:me"))
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data["display_name"], "Aisha")

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(
            email="aisha@example.com",
            display_name="Aisha",
            password="StrongPass!2048",
        )
        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "AISHA@example.com",
                "display_name": "Another Aisha",
                "password": "StrongPass!2048",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
