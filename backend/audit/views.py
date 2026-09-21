from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.models import AuditLog
from audit.serializers import AuditLogResponseSerializer


class AuditLogListAPIView(APIView):
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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