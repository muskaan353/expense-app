from rest_framework.routers import DefaultRouter

from apps.imports.views import ImportIssueViewSet, ImportSessionViewSet


router = DefaultRouter()
router.register("imports", ImportSessionViewSet, basename="import-session")
router.register("import-issues", ImportIssueViewSet, basename="import-issue")

urlpatterns = router.urls
