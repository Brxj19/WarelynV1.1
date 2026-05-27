from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.communication import Notification, NotificationCategory, NotificationType


class _NotificationRepo:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, values: dict) -> Notification:
        notification = Notification(**values)
        self.db.add(notification)
        self.db.flush()
        return notification

    def list_for_user(
        self,
        user_id: int,
        tenant_id: int | None,
        limit: int = 50,
        offset: int = 0,
        status: str = "all",
    ) -> list[Notification]:
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.tenant_id == tenant_id,
        )
        if status == "unread":
            query = query.where(Notification.is_read == False, Notification.cleared_at == None)
        elif status == "read":
            query = query.where(Notification.is_read == True, Notification.cleared_at == None)
        elif status == "cleared":
            query = query.where(Notification.cleared_at != None)
        else:
            # "all" - exclude cleared by default for main view
            query = query.where(Notification.cleared_at == None)
        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(query))

    def unread_count(self, user_id: int, tenant_id: int | None) -> int:
        return (
            self.db.scalar(
                select(func.count(Notification.id)).where(
                    Notification.user_id == user_id,
                    Notification.tenant_id == tenant_id,
                    Notification.is_read == False,
                    Notification.cleared_at == None,
                )
            )
            or 0
        )

    def get_by_id(self, notification_id: int) -> Notification | None:
        return self.db.get(Notification, notification_id)

    def mark_read(self, notification_id: int) -> None:
        self.db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        self.db.flush()

    def mark_all_read(self, user_id: int, tenant_id: int | None) -> None:
        self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.tenant_id == tenant_id,
                Notification.is_read == False,
                Notification.cleared_at == None,
            )
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        self.db.flush()

    def clear_one(self, notification_id: int, user_id: int, tenant_id: int | None) -> Notification | None:
        notification = self.get_by_id(notification_id)
        if notification is None or notification.user_id != user_id or notification.tenant_id != tenant_id:
            return None
        notification.cleared_at = datetime.now(timezone.utc)
        self.db.flush()
        return notification

    def clear_all(self, user_id: int, tenant_id: int | None) -> None:
        self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.tenant_id == tenant_id,
                Notification.cleared_at == None,
            )
            .values(cleared_at=datetime.now(timezone.utc))
        )
        self.db.flush()


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = _NotificationRepo(db)

    def create_notification(
        self,
        user_id: int,
        title: str,
        message: str | None = None,
        type: str = "INFO",
        category: str = "SYSTEM",
        tenant_id: int | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        action_url: str | None = None,
        priority: str = "normal",
    ) -> Notification:
        return self.repo.create(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": type,
                "category": category,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action_url": action_url,
                "priority": priority,
            }
        )

    def list_notifications(
        self,
        user_id: int,
        tenant_id: int | None,
        limit: int = 50,
        offset: int = 0,
        status: str = "all",
    ) -> list[Notification]:
        return self.repo.list_for_user(user_id, tenant_id, limit, offset, status)

    def unread_count(self, user_id: int, tenant_id: int | None = None) -> int:
        return self.repo.unread_count(user_id, tenant_id)

    def mark_read(self, user_id: int, notification_id: int, tenant_id: int | None = None) -> Notification | None:
        notification = self.repo.get_by_id(notification_id)
        if notification is None or notification.user_id != user_id:
            return None
        if tenant_id is not None and notification.tenant_id != tenant_id:
            return None
        self.repo.mark_read(notification_id)
        notification.is_read = True
        return notification

    def mark_all_read(self, user_id: int, tenant_id: int | None = None) -> None:
        self.repo.mark_all_read(user_id, tenant_id)

    def clear_one(self, notification_id: int, user_id: int, tenant_id: int | None = None) -> Notification | None:
        return self.repo.clear_one(notification_id, user_id, tenant_id)

    def clear_all(self, user_id: int, tenant_id: int | None = None) -> None:
        self.repo.clear_all(user_id, tenant_id)
