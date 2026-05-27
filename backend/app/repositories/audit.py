import json
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, values: dict[str, Any]) -> AuditLog:
        meta = values.get("metadata_json")
        if meta is not None and not isinstance(meta, str):
            values["metadata_json"] = json.dumps(meta, default=str)
        log = AuditLog(**values)
        self.db.add(log)
        self.db.flush()
        return log

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
    ) -> list[AuditLog]:
        query = select(AuditLog)
        if tenant_id is not None:
            query = query.where(AuditLog.tenant_id == tenant_id)
        if actor_user_id is not None:
            query = query.where(AuditLog.actor_user_id == actor_user_id)
        if action is not None:
            query = query.where(AuditLog.action == action)
        if entity_type is not None:
            query = query.where(AuditLog.entity_type == entity_type)
        if date_from is not None:
            query = query.where(AuditLog.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to is not None:
            query = query.where(AuditLog.created_at <= datetime.combine(date_to, datetime.max.time()))
        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(query))

    def count_logs(self, tenant_id: int | None = None) -> int:
        from sqlalchemy import func as sa_func
        query = select(sa_func.count(AuditLog.id))
        if tenant_id is not None:
            query = query.where(AuditLog.tenant_id == tenant_id)
        return self.db.scalar(query) or 0
