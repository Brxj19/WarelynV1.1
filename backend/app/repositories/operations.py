from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.operations import (
    OutboxEvent,
    OutboxEventStatus,
    PutawayTask,
    PutawayTaskStatus,
    ReorderRule,
    StockCountLine,
    StockCountSession,
    StockCountSessionStatus,
)


class ReorderRuleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, tenant_id: int) -> list[ReorderRule]:
        return list(self.db.scalars(select(ReorderRule).where(ReorderRule.tenant_id == tenant_id).order_by(ReorderRule.id)))

    def get(self, tenant_id: int, rule_id: int) -> ReorderRule | None:
        return self.db.scalar(select(ReorderRule).where(ReorderRule.id == rule_id, ReorderRule.tenant_id == tenant_id))

    def create(self, data: dict) -> ReorderRule:
        rule = ReorderRule(**data)
        self.db.add(rule)
        self.db.flush()
        return rule

    def update(self, rule: ReorderRule, data: dict) -> ReorderRule:
        for key, value in data.items():
            if value is not None:
                setattr(rule, key, value)
        self.db.flush()
        return rule

    def delete(self, rule: ReorderRule) -> None:
        self.db.delete(rule)
        self.db.flush()


class PutawayTaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, tenant_id: int, status: PutawayTaskStatus | None = None) -> list[PutawayTask]:
        q = select(PutawayTask).where(PutawayTask.tenant_id == tenant_id)
        if status is not None:
            q = q.where(PutawayTask.status == status)
        return list(self.db.scalars(q.order_by(PutawayTask.created_at.desc())))

    def get(self, tenant_id: int, task_id: int) -> PutawayTask | None:
        return self.db.scalar(select(PutawayTask).where(PutawayTask.id == task_id, PutawayTask.tenant_id == tenant_id))

    def create(self, data: dict) -> PutawayTask:
        task = PutawayTask(**data)
        self.db.add(task)
        self.db.flush()
        return task

    def update(self, task: PutawayTask, data: dict) -> PutawayTask:
        for key, value in data.items():
            if value is not None:
                setattr(task, key, value)
        self.db.flush()
        return task


class CycleCountRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_sessions(self, tenant_id: int) -> list[StockCountSession]:
        return list(
            self.db.scalars(
                select(StockCountSession)
                .where(StockCountSession.tenant_id == tenant_id)
                .options(selectinload(StockCountSession.lines))
                .order_by(StockCountSession.created_at.desc())
            )
        )

    def get_session(self, tenant_id: int, session_id: int) -> StockCountSession | None:
        return self.db.scalar(
            select(StockCountSession)
            .where(StockCountSession.id == session_id, StockCountSession.tenant_id == tenant_id)
            .options(selectinload(StockCountSession.lines))
        )

    def lock_session(self, tenant_id: int, session_id: int) -> StockCountSession | None:
        return self.db.scalar(
            select(StockCountSession)
            .where(StockCountSession.id == session_id, StockCountSession.tenant_id == tenant_id)
            .options(selectinload(StockCountSession.lines))
            .with_for_update()
        )

    def create_session(self, data: dict) -> StockCountSession:
        session = StockCountSession(**data)
        self.db.add(session)
        self.db.flush()
        return session

    def list_lines(self, tenant_id: int, session_id: int) -> list[StockCountLine]:
        return list(self.db.scalars(select(StockCountLine).where(StockCountLine.tenant_id == tenant_id, StockCountLine.session_id == session_id).order_by(StockCountLine.id)))

    def create_line(self, data: dict) -> StockCountLine:
        line = StockCountLine(**data)
        self.db.add(line)
        self.db.flush()
        return line

    def update_line(self, line: StockCountLine, data: dict) -> StockCountLine:
        for key, value in data.items():
            if value is not None:
                setattr(line, key, value)
        self.db.flush()
        return line


class OutboxRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_event(self, tenant_id: int | None, event_type: str, payload: dict) -> OutboxEvent:
        event = OutboxEvent(tenant_id=tenant_id, event_type=event_type, payload_json=payload)
        self.db.add(event)
        self.db.flush()
        return event

    def list_pending(self, limit: int = 50) -> list[OutboxEvent]:
        return list(self.db.scalars(select(OutboxEvent).where(OutboxEvent.status == OutboxEventStatus.PENDING).order_by(OutboxEvent.created_at).limit(limit)))

    def mark_processed(self, event: OutboxEvent) -> None:
        event.status = OutboxEventStatus.PROCESSED
        event.processed_at = datetime.now(UTC)
        self.db.flush()

    def mark_failed(self, event: OutboxEvent, error: str) -> None:
        event.status = OutboxEventStatus.FAILED
        event.attempts += 1
        event.last_error = error
        self.db.flush()
