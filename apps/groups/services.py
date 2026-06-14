from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.groups.models import Group, GroupMembership


@transaction.atomic
def create_group(*, owner, name, description="", base_currency="INR"):
    group = Group.objects.create(
        owner=owner,
        name=name,
        description=description,
        base_currency=base_currency,
    )
    GroupMembership.objects.create(
        group=group,
        user=owner,
        role=GroupMembership.Role.OWNER,
        joined_at=timezone.now(),
    )
    return group


@transaction.atomic
def archive_group(*, group):
    if group.archived_at is None:
        group.archived_at = timezone.now()
        group.save(update_fields=("archived_at", "updated_at"))
    return group


@transaction.atomic
def add_membership(*, group, user, role, joined_at, left_at=None):
    overlapping = (
        GroupMembership.objects.select_for_update()
        .filter(group=group, user=user)
        .filter(Q(left_at__isnull=True) | Q(left_at__gt=joined_at))
    )
    if left_at is not None:
        overlapping = overlapping.filter(joined_at__lt=left_at)
    if overlapping.exists():
        raise ValidationError(
            {"membership": "This period overlaps an existing membership."}
        )
    return GroupMembership.objects.create(
        group=group,
        user=user,
        role=role,
        joined_at=joined_at,
        left_at=left_at,
    )


@transaction.atomic
def end_membership(*, membership, left_at):
    locked = GroupMembership.objects.select_for_update().get(pk=membership.pk)
    if locked.role == GroupMembership.Role.OWNER:
        raise ValidationError({"membership": "The owner membership cannot be ended."})
    if left_at <= locked.joined_at:
        raise ValidationError({"left_at": "left_at must be after joined_at."})
    locked.left_at = left_at
    locked.full_clean()
    locked.save(update_fields=("left_at",))
    return locked
