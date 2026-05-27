from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.db.session import get_db
from app.dependencies.auth import require_tenant_user
from app.repositories.notification import NotificationRepository
from app.schemas.communication import NotificationRead
from app.services.auth import UserContext

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    status: str = Query("all", pattern="^(all|unread|read|cleared)$"),
    limit: int = 50,
    offset: int = 0,
    context: UserContext = Depends(require_tenant_user),
    db: Session = Depends(get_db),
) -> list[NotificationRead]:
    return NotificationRepository(db).list_notifications(
        context.user.id, context.tenant_id, limit, offset, status
    )


@router.get("/unread-count")
def unread_notification_count(
    context: UserContext = Depends(require_tenant_user),
    db: Session = Depends(get_db),
) -> dict:
    count = NotificationRepository(db).unread_count(context.user.id, context.tenant_id)
    return {"count": count}


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: int,
    context: UserContext = Depends(require_tenant_user),
    db: Session = Depends(get_db),
) -> NotificationRead:
    result = NotificationRepository(db).mark_read(context.user.id, notification_id, context.tenant_id)
    if result is None:
        raise AppError("NOTIFICATION_NOT_FOUND", "Notification was not found.", 404)
    return result


@router.post("/read-all")
def mark_all_notifications_read(
    context: UserContext = Depends(require_tenant_user),
    db: Session = Depends(get_db),
) -> dict:
    NotificationRepository(db).mark_all_read(context.user.id, context.tenant_id)
    return {"success": True}


@router.post("/{notification_id}/clear", response_model=NotificationRead)
def clear_notification(
    notification_id: int,
    context: UserContext = Depends(require_tenant_user),
    db: Session = Depends(get_db),
) -> NotificationRead:
    result = NotificationRepository(db).clear_one(notification_id, context.user.id, context.tenant_id)
    if result is None:
        raise AppError("NOTIFICATION_NOT_FOUND", "Notification was not found.", 404)
    return result


@router.post("/clear-all")
def clear_all_notifications(
    context: UserContext = Depends(require_tenant_user),
    db: Session = Depends(get_db),
) -> dict:
    NotificationRepository(db).clear_all(context.user.id, context.tenant_id)
    return {"success": True}
