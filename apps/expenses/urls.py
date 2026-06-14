from rest_framework.routers import DefaultRouter

from apps.expenses.views import ExchangeRateViewSet, ExpenseViewSet


router = DefaultRouter()
router.register("exchange-rates", ExchangeRateViewSet, basename="exchange-rate")
router.register("expenses", ExpenseViewSet, basename="expense")

urlpatterns = router.urls
