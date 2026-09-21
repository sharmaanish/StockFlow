from audit.models import AuditLog


def create_audit_log(
    *,
    tenant,
    action,
    entity_type,
    entity_id,
    user=None,
    metadata=None,
):
    return AuditLog.objects.create(
        tenant=tenant,
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        metadata=metadata or {},
    )