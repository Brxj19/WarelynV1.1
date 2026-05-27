from datetime import date

from sqlalchemy.orm import Session

from app.services.operations import ExpireBatchesService


def run_expire_batches(db: Session, tenant_id: int) -> dict:
    return ExpireBatchesService(db).run(tenant_id)
