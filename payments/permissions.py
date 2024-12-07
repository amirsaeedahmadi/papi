from rest_framework.permissions import BasePermission

from users.permissions import EmailVerified
from users.permissions import MobileVerified


class HasAccountableRole(BasePermission):
    def has_permission(self, request, view):
        return request.is_admin_host and (request.user.is_superuser or
                                       request.user.has_perm(
            "payments.accountable"
        ))


class HasAccountableRoleOrEmailAndMobileVerified(BasePermission):
    def has_permission(self, request, view):
        return HasAccountableRole().has_permission(request, view) or (
            EmailVerified().has_permission(request, view)
            and MobileVerified().has_permission(request, view)
        )
