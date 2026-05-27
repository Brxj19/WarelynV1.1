from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class TenantScopedRepository(Generic[ModelT]):
    def __init__(self, db: Session, model: type[ModelT]) -> None:
        self.db = db
        self.model = model

    def list_by_tenant(self, tenant_id: int) -> list[ModelT]:
        return list(self.db.scalars(select(self.model).where(self.model.tenant_id == tenant_id)))

    def get_by_id_for_tenant(self, tenant_id: int, record_id: int) -> ModelT | None:
        return self.db.scalar(select(self.model).where(self.model.id == record_id, self.model.tenant_id == tenant_id))

    def create_for_tenant(self, tenant_id: int, values: dict[str, Any]) -> ModelT:
        record = self.model(tenant_id=tenant_id, **values)
        self.db.add(record)
        return record

    def update_for_tenant(self, tenant_id: int, record_id: int, values: dict[str, Any]) -> ModelT | None:
        record = self.get_by_id_for_tenant(tenant_id, record_id)
        if record is None:
            return None
        for key, value in values.items():
            setattr(record, key, value)
        return record

    def soft_delete_for_tenant(self, tenant_id: int, record_id: int) -> ModelT | None:
        record = self.get_by_id_for_tenant(tenant_id, record_id)
        if record is None:
            return None
        record.status = "ARCHIVED"
        return record
