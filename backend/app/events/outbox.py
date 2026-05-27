from sqlalchemy.orm import Session

from app.repositories.operations import OutboxRepository


def publish_event(db: Session, tenant_id: int | None, event_type: str, payload: dict):
    repo = OutboxRepository(db)
    return repo.create_event(tenant_id, event_type, payload)
