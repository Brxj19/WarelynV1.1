from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.audit import AuditLogRepository


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AuditLogRepository(db)

    def create_log(self, values: dict[str, Any]) -> None:
        self.repository.create(values)

    def list_logs(
        self,
        tenant_id: int | None = None,
        actor_user_id: int | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        logs = self.repository.list_logs(tenant_id, actor_user_id, action, entity_type, date_from, date_to, limit, offset)
        return [
            {
                "id": log.id,
                "tenant_id": log.tenant_id,
                "actor_user_id": log.actor_user_id,
                "actor_role": log.actor_role,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "request_id": log.request_id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "metadata_json": log.metadata_json,
                "created_at": log.created_at,
            }
            for log in logs
        ]
