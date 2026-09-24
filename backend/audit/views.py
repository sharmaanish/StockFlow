from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsManager
from audit.models import AuditLog
from audit.serializers import AuditLogResponseSerializer


class AuditLogListAPIView(APIView):
    """
    List audit logs belonging to the authenticated user's tenant.

    Allowed roles:
        Admin
        Manager
    """

    permission_classes = [IsManager]

    def get(self, request):
        tenant = request.user.tenant

        audit_logs = (
            AuditLog.objects
            .filter(tenant=tenant)
            .select_related("user")
            .order_by("-created_at")
        )

        serializer = AuditLogResponseSerializer(
            audit_logs,
            many=True,
        )

        return Response(serializer.data)


class AuditLogRetrieveAPIView(APIView):
    """
    Retrieve a single audit log belonging to the
    authenticated user's tenant.

    Allowed roles:
        Admin
        Manager
    """

    permission_classes = [IsManager]

    def get(self, request, audit_id):
        tenant = request.user.tenant

        audit_log = get_object_or_404(
            AuditLog,
            id=audit_id,
            tenant=tenant,
        )

        serializer = AuditLogResponseSerializer(
            audit_log,
        )

        return Response(serializer.data)