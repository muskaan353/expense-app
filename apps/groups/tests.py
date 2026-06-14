from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.groups.models import Group


class GroupApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            display_name="Owner",
            password="StrongPass!2048",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            display_name="Other",
            password="StrongPass!2048",
        )
        self.client.force_authenticate(self.owner)

    def test_owner_can_create_and_archive_group(self):
        create_response = self.client.post(
            reverse("group-list"),
            {"name": "Flatmates", "base_currency": "inr"},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["base_currency"], "INR")

        archive_response = self.client.post(
            reverse("group-archive", args=[create_response.data["id"]])
        )
        self.assertEqual(archive_response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(archive_response.data["archived_at"])

    def test_user_cannot_read_another_users_group(self):
        group = Group.objects.create(name="Private", owner=self.other_user)
        response = self.client.get(reverse("group-detail", args=[group.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
