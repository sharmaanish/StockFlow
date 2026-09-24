from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Allows access only to StockFlow admins.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsManager(BasePermission):
    """
    Allows admins and managers.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in {
                "admin",
                "manager",
            }
        )


class IsStaff(BasePermission):
    """
    Allows admins, managers, and staff.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in {
                "admin",
                "manager",
                "staff",
            }
        )


class IsReadOnly(BasePermission):
    """
    Allows all authenticated users to perform read operations.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.method in {
                "GET",
                "HEAD",
                "OPTIONS",
            }
        )