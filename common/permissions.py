from rest_framework import permissions

from apps.users.models import User


class IsAdminUserLevel(permissions.BasePermission):
    message = "仅管理员可执行该操作"

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.user_level == User.Level.ADMIN
        )
