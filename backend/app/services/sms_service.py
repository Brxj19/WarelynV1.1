import logging

from sqlalchemy.orm import Session

from app.models.communication import SMSOutbox, SMSOutboxStatus

logger = logging.getLogger(__name__)


class SMSDevOutboxService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def send(self, phone: str, message: str, purpose: str | None = None, tenant_id: int | None = None, user_id: int | None = None) -> SMSOutbox:
        outbox = SMSOutbox(
            tenant_id=tenant_id,
            user_id=user_id,
            phone=phone,
            message=message,
            purpose=purpose,
            status=SMSOutboxStatus.PENDING,
        )
        self.db.add(outbox)
        self.db.flush()
        outbox.status = SMSOutboxStatus.SENT
        self.db.flush()
        return outbox
