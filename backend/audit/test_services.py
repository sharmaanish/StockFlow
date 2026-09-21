from rest_framework.test import APITestCase

from accounts.models import User
from audit.models import AuditLog
from audit.services import create_audit_log
from tenants.models import Tenant


class AuditServiceTestCase(APITestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
        )

        self.user = User.objects.create_user(
            tenant=self.tenant,
            email="audit-test@example.com",
            password="test-password",
        )

    def test_create_audit_log(self):
        audit_log = create_audit_log(
            tenant=self.tenant,
            user=self.user,
            action="ORDER_CREATED",
            entity_type="Order",
            entity_id="order-123",
        )

        self.assertEqual(
            audit_log.tenant,
            self.tenant,
        )

        self.assertEqual(
            audit_log.user,
            self.user,
        )

        self.assertEqual(
            audit_log.action,
            "ORDER_CREATED",
        )

        self.assertEqual(
            audit_log.entity_type,
            "Order",
        )

        self.assertEqual(
            audit_log.entity_id,
            "order-123",
        )

        self.assertEqual(
            audit_log.metadata,
            {},
        )

    def test_create_audit_log_with_metadata(self):
        audit_log = create_audit_log(
            tenant=self.tenant,
            user=self.user,
            action="ORDER_STATUS_CHANGED",
            entity_type="Order",
            entity_id="order-123",
            metadata={
                "previous_status": "pending",
                "new_status": "confirmed",
            },
        )

        self.assertEqual(
            audit_log.metadata["previous_status"],
            "pending",
        )

        self.assertEqual(
            audit_log.metadata["new_status"],
            "confirmed",
        )

    def test_create_audit_log_without_user(self):
        audit_log = create_audit_log(
            tenant=self.tenant,
            action="SYSTEM_ACTION",
            entity_type="Order",
            entity_id="order-123",
        )

        self.assertIsNone(
            audit_log.user,
        )

    def test_entity_id_is_stored_as_string(self):
        audit_log = create_audit_log(
            tenant=self.tenant,
            action="ORDER_CREATED",
            entity_type="Order",
            entity_id=12345,
        )

        self.assertEqual(
            audit_log.entity_id,
            "12345",
        )

    def test_metadata_defaults_to_empty_dictionary(self):
        audit_log = create_audit_log(
            tenant=self.tenant,
            action="ORDER_CREATED",
            entity_type="Order",
            entity_id="order-123",
        )

        self.assertEqual(
            audit_log.metadata,
            {},
        )