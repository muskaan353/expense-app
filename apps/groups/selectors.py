from django.db.models import Q
from django.utils import timezone

from apps.groups.models import Group


def accessible_groups_for(*, user, at=None):
    at = at or timezone.now()
    return (
        Group.objects.filter(
            Q(owner=user)
            | Q(memberships__user=user, memberships__joined_at__lte=at)
            & (
                Q(memberships__left_at__isnull=True)
                | Q(memberships__left_at__gt=at)
            )
        )
        .select_related("owner")
        .distinct()
    )
