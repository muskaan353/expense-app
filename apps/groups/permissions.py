from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsGroupOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.owner_id == request.user.id
