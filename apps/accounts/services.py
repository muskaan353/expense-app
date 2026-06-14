from django.db import transaction

from apps.accounts.models import User


@transaction.atomic
def register_user(*, email, display_name, password):
    return User.objects.create_user(
        email=email,
        display_name=display_name,
        password=password,
    )
