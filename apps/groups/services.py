from django.db import transaction
from django.utils import timezone

from apps.groups.models import Group


@transaction.atomic
def create_group(*, owner, name, description="", base_currency="INR"):
    return Group.objects.create(
        owner=owner,
        name=name,
        description=description,
        base_currency=base_currency,
    )


@transaction.atomic
def archive_group(*, group):
    if group.archived_at is None:
        group.archived_at = timezone.now()
        group.save(update_fields=("archived_at", "updated_at"))
    return group
