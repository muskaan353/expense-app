from rest_framework.routers import DefaultRouter

from apps.settlements.views import SettlementViewSet


router = DefaultRouter()
router.register("settlements", SettlementViewSet, basename="settlement")

urlpatterns = router.urls
