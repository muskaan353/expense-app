from django.urls import path

from apps.balances.views import GroupBalanceView


urlpatterns = [
    path(
        "groups/<int:group_id>/balances/",
        GroupBalanceView.as_view(),
        name="group-balances",
    )
]
