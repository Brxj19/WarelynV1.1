import logging

from sqlalchemy.orm import Session

from app.models.auth import UserRole
from app.repositories.notification import NotificationRepository
from app.repositories.users import UsersRepository

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = NotificationRepository(db)
        self.users = UsersRepository(db)

    def notify_user(
        self,
        tenant_id: int,
        user_id: int,
        title: str,
        message: str | None = None,
        type: str = "INFO",
        category: str = "SYSTEM",
        entity_type: str | None = None,
        entity_id: int | str | None = None,
        action_url: str | None = None,
        priority: str = "normal",
    ) -> None:
        try:
            self.repo.create_notification(
                user_id=user_id,
                tenant_id=tenant_id,
                title=title,
                message=message,
                type=type,
                category=category,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                action_url=action_url,
                priority=priority,
            )
            self.db.commit()
        except Exception:
            logger.exception("Failed to send notification to user %s", user_id)
            self.db.rollback()

    def notify_role(
        self,
        tenant_id: int,
        role: str,
        title: str,
        message: str | None = None,
        type: str = "INFO",
        category: str = "SYSTEM",
        entity_type: str | None = None,
        entity_id: int | str | None = None,
        action_url: str | None = None,
        priority: str = "normal",
        exclude_user_id: int | None = None,
    ) -> None:
        try:
            users = self.users.list_users(tenant_id, role=UserRole(role))
            for user in users:
                if exclude_user_id is not None and user.id == exclude_user_id:
                    continue
                self.repo.create_notification(
                    user_id=user.id,
                    tenant_id=tenant_id,
                    title=title,
                    message=message,
                    type=type,
                    category=category,
                    entity_type=entity_type,
                    entity_id=str(entity_id) if entity_id is not None else None,
                    action_url=action_url,
                    priority=priority,
                )
            self.db.commit()
        except Exception:
            logger.exception("Failed to send notification to role %s", role)
            self.db.rollback()

    def notify_roles(
        self,
        tenant_id: int,
        roles: list[str],
        title: str,
        message: str | None = None,
        type: str = "INFO",
        category: str = "SYSTEM",
        entity_type: str | None = None,
        entity_id: int | str | None = None,
        action_url: str | None = None,
        priority: str = "normal",
        exclude_user_id: int | None = None,
    ) -> None:
        try:
            sent_ids: set[int] = set()
            for role in roles:
                users = self.users.list_users(tenant_id, role=UserRole(role))
                for user in users:
                    if user.id in sent_ids:
                        continue
                    if exclude_user_id is not None and user.id == exclude_user_id:
                        continue
                    sent_ids.add(user.id)
                    self.repo.create_notification(
                        user_id=user.id,
                        tenant_id=tenant_id,
                        title=title,
                        message=message,
                        type=type,
                        category=category,
                        entity_type=entity_type,
                        entity_id=str(entity_id) if entity_id is not None else None,
                        action_url=action_url,
                        priority=priority,
                    )
            self.db.commit()
        except Exception:
            logger.exception("Failed to send notification to roles %s", roles)
            self.db.rollback()
