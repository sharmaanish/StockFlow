from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from audit.models import AuditLog
from tenants.models import Tenant


class AuditLogAPITestCase(APITestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
        )

        self.other_tenant = Tenant.objects.create(
            name="Other Tenant",
            slug="other-tenant",
        )

        self.user = User.objects.create_user(
            email="audit@test.com",
            password="testpassword123",
            tenant=self.tenant,
        )

        self.other_user = User.objects.create_user(
            email="other@test.com",
            password="testpassword123",
            tenant=self.other_tenant,
        )

        self.audit_log = AuditLog.objects.create(
            tenant=self.tenant,
            user=self.user,
            action="ORDER_CREATED",
            entity_type="Order",
            entity_id="order-123",
            metadata={
                "total": "100.00",
            },
        )

        self.other_audit_log = AuditLog.objects.create(
            tenant=self.other_tenant,
            user=self.other_user,
            action="ORDER_CREATED",
            entity_type="Order",
            entity_id="other-order-123",
            metadata={
                "total": "200.00",
            },
        )

    def test_list_requires_authentication(self):
        response = self.client.get(
            "/api/v1/audit-logs/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_list_returns_only_current_tenant_logs(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            "/api/v1/audit-logs/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["id"],
            str(self.audit_log.id),
        )

    def test_list_includes_audit_log_fields(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            "/api/v1/audit-logs/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        audit_log = response.data[0]

        self.assertEqual(
            audit_log["action"],
            "ORDER_CREATED",
        )

        self.assertEqual(
            audit_log["entity_type"],
            "Order",
        )

        self.assertEqual(
            audit_log["entity_id"],
            "order-123",
        )

        self.assertEqual(
            audit_log["metadata"],
            {
                "total": "100.00",
            },
        )

        self.assertEqual(
            audit_log["user"],
            str(self.user.id),
        )

    def test_retrieve_audit_log(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            f"/api/v1/audit-logs/{self.audit_log.id}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            str(self.audit_log.id),
        )

        self.assertEqual(
            response.data["action"],
            "ORDER_CREATED",
        )

    def test_retrieve_other_tenant_log_returns_404(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            f"/api/v1/audit-logs/{self.other_audit_log.id}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_retrieve_requires_authentication(self):
        response = self.client.get(
            f"/api/v1/audit-logs/{self.audit_log.id}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )