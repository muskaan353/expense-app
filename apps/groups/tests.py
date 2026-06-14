from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.groups.models import Group, GroupMembership
from apps.groups.services import add_membership, create_group


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

    def test_group_creation_records_owner_membership(self):
        group = create_group(owner=self.owner, name="Timeline")
        membership = group.memberships.get(user=self.owner)
        self.assertEqual(membership.role, GroupMembership.Role.OWNER)
        self.assertIsNone(membership.left_at)

    def test_active_member_can_read_group_but_past_member_cannot(self):
        now = timezone.now()
        group = create_group(owner=self.owner, name="Flatmates")
        membership = add_membership(
            group=group,
            user=self.other_user,
            role=GroupMembership.Role.MEMBER,
            joined_at=now - timedelta(days=10),
        )

        self.client.force_authenticate(self.other_user)
        self.assertEqual(
            self.client.get(reverse("group-detail", args=[group.id])).status_code,
            status.HTTP_200_OK,
        )

        membership.left_at = now - timedelta(days=1)
        membership.save(update_fields=("left_at",))
        self.assertEqual(
            self.client.get(reverse("group-detail", args=[group.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_overlapping_membership_period_is_rejected(self):
        now = timezone.now()
        group = create_group(owner=self.owner, name="Flatmates")
        add_membership(
            group=group,
            user=self.other_user,
            role=GroupMembership.Role.MEMBER,
            joined_at=now - timedelta(days=20),
            left_at=now - timedelta(days=5),
        )
        with self.assertRaisesMessage(Exception, "overlaps"):
            add_membership(
                group=group,
                user=self.other_user,
                role=GroupMembership.Role.MEMBER,
                joined_at=now - timedelta(days=10),
            )
