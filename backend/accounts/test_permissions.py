from django.test import TestCase
from rest_framework.test import APIRequestFactory

from accounts.models import User
from accounts.permissions import (
    IsAdmin,
    IsManager,
    IsReadOnly,
    IsStaff,
)
from tenants.models import Tenant


class RBACPermissionTestCase(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
        )

        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpassword123",
            tenant=self.tenant,
            role=User.Role.ADMIN,
        )

        self.manager_user = User.objects.create_user(
            email="manager@test.com",
            password="testpassword123",
            tenant=self.tenant,
            role=User.Role.MANAGER,
        )

        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            password="testpassword123",
            tenant=self.tenant,
            role=User.Role.STAFF,
        )

        self.viewer_user = User.objects.create_user(
            email="viewer@test.com",
            password="testpassword123",
            tenant=self.tenant,
            role=User.Role.VIEWER,
        )

        self.factory = APIRequestFactory()

    def test_admin_permission(self):
        request = self.factory.get("/")
        request.user = self.admin_user

        permission = IsAdmin()

        self.assertTrue(
            permission.has_permission(request, None)
        )

    def test_manager_permission_allows_admin_and_manager(self):
        permission = IsManager()

        admin_request = self.factory.get("/")
        admin_request.user = self.admin_user

        manager_request = self.factory.get("/")
        manager_request.user = self.manager_user

        staff_request = self.factory.get("/")
        staff_request.user = self.staff_user

        viewer_request = self.factory.get("/")
        viewer_request.user = self.viewer_user

        self.assertTrue(
            permission.has_permission(
                admin_request,
                None,
            )
        )

        self.assertTrue(
            permission.has_permission(
                manager_request,
                None,
            )
        )

        self.assertFalse(
            permission.has_permission(
                staff_request,
                None,
            )
        )

        self.assertFalse(
            permission.has_permission(
                viewer_request,
                None,
            )
        )

    def test_staff_permission_allows_admin_manager_and_staff(self):
        permission = IsStaff()

        admin_request = self.factory.get("/")
        admin_request.user = self.admin_user

        manager_request = self.factory.get("/")
        manager_request.user = self.manager_user

        staff_request = self.factory.get("/")
        staff_request.user = self.staff_user

        viewer_request = self.factory.get("/")
        viewer_request.user = self.viewer_user

        self.assertTrue(
            permission.has_permission(
                admin_request,
                None,
            )
        )

        self.assertTrue(
            permission.has_permission(
                manager_request,
                None,
            )
        )

        self.assertTrue(
            permission.has_permission(
                staff_request,
                None,
            )
        )

        self.assertFalse(
            permission.has_permission(
                viewer_request,
                None,
            )
        )

    def test_read_only_permission_allows_all_roles_for_get(self):
        permission = IsReadOnly()

        for user in [
            self.admin_user,
            self.manager_user,
            self.staff_user,
            self.viewer_user,
        ]:
            request = self.factory.get("/")
            request.user = user

            self.assertTrue(
                permission.has_permission(
                    request,
                    None,
                )
            )

    def test_read_only_permission_allows_all_roles_for_head(self):
        permission = IsReadOnly()

        for user in [
            self.admin_user,
            self.manager_user,
            self.staff_user,
            self.viewer_user,
        ]:
            request = self.factory.head("/")
            request.user = user

            self.assertTrue(
                permission.has_permission(
                    request,
                    None,
                )
            )

    def test_read_only_permission_allows_all_roles_for_options(self):
        permission = IsReadOnly()

        for user in [
            self.admin_user,
            self.manager_user,
            self.staff_user,
            self.viewer_user,
        ]:
            request = self.factory.options("/")
            request.user = user

            self.assertTrue(
                permission.has_permission(
                    request,
                    None,
                )
            )

    def test_read_only_permission_denies_write_methods(self):
        permission = IsReadOnly()

        for method in [
            "post",
            "put",
            "patch",
            "delete",
        ]:
            for user in [
                self.admin_user,
                self.manager_user,
                self.staff_user,
                self.viewer_user,
            ]:
                request = getattr(
                    self.factory,
                    method,
                )("/")

                request.user = user

                self.assertFalse(
                    permission.has_permission(
                        request,
                        None,
                    )
                )

    def test_admin_permission_denies_non_admin_roles(self):
        permission = IsAdmin()

        for user in [
            self.manager_user,
            self.staff_user,
            self.viewer_user,
        ]:
            request = self.factory.get("/")
            request.user = user

            self.assertFalse(
                permission.has_permission(
                    request,
                    None,
                )
            )