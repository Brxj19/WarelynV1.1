import logging

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import get_password_hash
from app.models.auth import User, UserRole, UserStatus
from app.models.documents import DocumentTemplateChannel, DocumentTemplateKey
from app.repositories.audit import AuditLogRepository
from app.repositories.notification import NotificationRepository
from app.repositories.users import UsersRepository
from app.schemas.users import UserCreate, UserUpdate
from app.services.documents import DocumentTemplateService
from app.services.email_service import send_email
from app.utils.phone import normalize_phone, validate_phone

logger = logging.getLogger(__name__)


ALLOWED_ROLES_FOR_CREATION = {
    UserRole.TENANT_ADMIN,
    UserRole.INVENTORY_MANAGER,
    UserRole.SALES_STAFF,
    UserRole.PURCHASE_STAFF,
    UserRole.VIEWER,
}


class UsersService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UsersRepository(db)
        self.audit = AuditLogRepository(db)
        self.notifications = NotificationRepository(db)

    def list_users(
        self,
        tenant_id: int,
        search: str | None = None,
        role: UserRole | None = None,
        status: UserStatus | None = None,
    ) -> list[User]:
        return self.repo.list_users(tenant_id, search=search, role=role, status=status)

    def get_user(self, tenant_id: int, user_id: int) -> User:
        user = self.repo.get_user(tenant_id, user_id)
        if not user:
            raise AppError("USER_NOT_FOUND", "User not found.", 404)
        return user

    def create_user(self, tenant_id: int, actor_user_id: int, data: UserCreate) -> User:
        if data.role == UserRole.SUPER_ADMIN:
            raise AppError("FORBIDDEN", "Cannot create a user with SUPER_ADMIN role.", 403)
        if data.role not in ALLOWED_ROLES_FOR_CREATION:
            raise AppError("INVALID_ROLE", "Invalid role for user creation.", 400)

        existing = self.repo.get_by_email(str(data.email))
        if existing:
            raise AppError("DUPLICATE_EMAIL", "A user with this email already exists.", 409)

        # Phone validation
        phone = data.phone
        if phone:
            phone = normalize_phone(phone)
            valid, error = validate_phone(phone)
            if not valid:
                raise AppError("INVALID_PHONE", error, 400)

        user = self.repo.create_user(
            tenant_id=tenant_id,
            name=data.name,
            email=str(data.email),
            phone=phone,
            password_hash=get_password_hash(data.password),
            role=data.role,
        )

        self.audit.create({
            "tenant_id": tenant_id,
            "actor_user_id": actor_user_id,
            "actor_role": UserRole.TENANT_ADMIN.value,
            "action": "USER_CREATED",
            "entity_type": "User",
            "entity_id": str(user.id),
            "metadata_json": {"name": user.name, "email": user.email, "role": user.role.value},
        })

        self.db.commit()
        self.db.refresh(user)

        # Send welcome email (non-blocking)
        tenant_name = self._get_tenant_name(tenant_id)
        self._send_user_email(tenant_id, user, DocumentTemplateKey.ACCOUNT_CREATED, {
            "user_name": user.name,
            "email": user.email,
            "role": user.role.value,
            "tenant_name": tenant_name,
            "login_url": "/login",
        })

        # Create notifications
        self._notify_user_event(
            tenant_id, user.id, actor_user_id,
            "Account Created",
            f"Welcome to {tenant_name}!",
        )

        return user

    def update_user(self, tenant_id: int, actor_user_id: int, user_id: int, data: UserUpdate) -> User:
        user = self.get_user(tenant_id, user_id)

        if data.role == UserRole.SUPER_ADMIN:
            raise AppError("FORBIDDEN", "Cannot assign SUPER_ADMIN role.", 403)

        if user_id == actor_user_id and data.role is not None and data.role != user.role:
            raise AppError("FORBIDDEN", "Cannot change your own role.", 403)

        update_values = data.model_dump(exclude_unset=True)
        if not update_values:
            return user

        # Phone validation
        if "phone" in update_values and update_values["phone"]:
            update_values["phone"] = normalize_phone(update_values["phone"])
            valid, error = validate_phone(update_values["phone"])
            if not valid:
                raise AppError("INVALID_PHONE", error, 400)

        old_role = user.role
        self.repo.update_user(user, **update_values)

        self.audit.create({
            "tenant_id": tenant_id,
            "actor_user_id": actor_user_id,
            "actor_role": UserRole.TENANT_ADMIN.value,
            "action": "USER_UPDATED",
            "entity_type": "User",
            "entity_id": str(user.id),
            "metadata_json": {"updated_fields": list(update_values.keys())},
        })

        self.db.commit()
        self.db.refresh(user)

        # If role changed, send notification
        if "role" in update_values and update_values["role"] is not None and old_role != user.role:
            tenant_name = self._get_tenant_name(tenant_id)
            self._send_user_email(tenant_id, user, DocumentTemplateKey.ROLE_CHANGED, {
                "user_name": user.name,
                "old_role": old_role.value,
                "new_role": user.role.value,
                "tenant_name": tenant_name,
            })
            self._notify_user_event(
                tenant_id, user.id, actor_user_id,
                "Role Changed",
                f"Role changed from {old_role.value} to {user.role.value}.",
            )

        return user

    def disable_user(self, tenant_id: int, actor_user_id: int, user_id: int) -> User:
        if user_id == actor_user_id:
            raise AppError("FORBIDDEN", "Cannot disable yourself.", 403)

        user = self.get_user(tenant_id, user_id)
        if user.status == UserStatus.DISABLED:
            raise AppError("ALREADY_DISABLED", "User is already disabled.", 400)

        self.repo.disable_user(user)

        self.audit.create({
            "tenant_id": tenant_id,
            "actor_user_id": actor_user_id,
            "actor_role": UserRole.TENANT_ADMIN.value,
            "action": "USER_DISABLED",
            "entity_type": "User",
            "entity_id": str(user.id),
            "metadata_json": {"name": user.name, "email": user.email},
        })

        self.db.commit()
        self.db.refresh(user)

        # Send disabled email (non-blocking)
        tenant_name = self._get_tenant_name(tenant_id)
        self._send_user_email(tenant_id, user, DocumentTemplateKey.USER_DISABLED, {
            "user_name": user.name,
            "tenant_name": tenant_name,
            "reason": "",
        })
        self._notify_user_event(
            tenant_id, user.id, actor_user_id,
            "Account Disabled",
            f"{user.name}'s account has been disabled.",
        )

        return user

    def enable_user(self, tenant_id: int, actor_user_id: int, user_id: int) -> User:
        user = self.get_user(tenant_id, user_id)
        if user.status == UserStatus.ACTIVE:
            raise AppError("ALREADY_ACTIVE", "User is already active.", 400)

        self.repo.enable_user(user)

        self.audit.create({
            "tenant_id": tenant_id,
            "actor_user_id": actor_user_id,
            "actor_role": UserRole.TENANT_ADMIN.value,
            "action": "USER_ENABLED",
            "entity_type": "User",
            "entity_id": str(user.id),
            "metadata_json": {"name": user.name, "email": user.email},
        })

        self.db.commit()
        self.db.refresh(user)

        # Send enabled email (non-blocking)
        tenant_name = self._get_tenant_name(tenant_id)
        self._send_user_email(tenant_id, user, DocumentTemplateKey.USER_ENABLED, {
            "user_name": user.name,
            "tenant_name": tenant_name,
        })
        self._notify_user_event(
            tenant_id, user.id, actor_user_id,
            "Account Enabled",
            f"{user.name}'s account has been re-enabled.",
        )

        return user

    def reset_password(self, tenant_id: int, actor_user_id: int, user_id: int, new_password: str) -> User:
        user = self.get_user(tenant_id, user_id)
        user.password_hash = get_password_hash(new_password)
        self.db.flush()

        self.audit.create({
            "tenant_id": tenant_id,
            "actor_user_id": actor_user_id,
            "actor_role": UserRole.TENANT_ADMIN.value,
            "action": "USER_PASSWORD_RESET",
            "entity_type": "User",
            "entity_id": str(user.id),
            "metadata_json": {"name": user.name, "email": user.email},
        })

        self.db.commit()
        self.db.refresh(user)

        # Send password reset email (non-blocking)
        tenant_name = self._get_tenant_name(tenant_id)
        self._send_user_email(tenant_id, user, DocumentTemplateKey.PASSWORD_RESET, {
            "user_name": user.name,
            "tenant_name": tenant_name,
        })
        self._notify_user_event(
            tenant_id, user.id, actor_user_id,
            "Password Reset",
            f"Password was reset for {user.name}.",
        )

        return user

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_tenant_name(self, tenant_id: int) -> str:
        """Get tenant company name, fallback to 'Warelyn'."""
        from app.models.auth import Tenant
        tenant = self.db.get(Tenant, tenant_id)
        if tenant and hasattr(tenant, "company_name") and tenant.company_name:
            return tenant.company_name
        return "Warelyn"

    def _send_user_email(
        self,
        tenant_id: int,
        user: User,
        template_key: DocumentTemplateKey,
        context: dict,
    ) -> None:
        """Render and send a user management email. Never raises."""
        try:
            template_service = DocumentTemplateService(self.db)
            rendered = template_service.render_by_key(
                tenant_id=tenant_id,
                channel=DocumentTemplateChannel.EMAIL,
                template_key=template_key,
                context=context,
            )
            send_email(
                to_email=user.email,
                subject=rendered["subject"] or "",
                body_text=rendered.get("text") or "",
                body_html=rendered.get("body"),
            )
        except Exception as exc:
            logger.warning(f"Failed to send user email ({template_key.value}): {exc}")

    def _notify_user_event(
        self,
        tenant_id: int,
        target_user_id: int,
        actor_user_id: int,
        title: str,
        message: str,
    ) -> None:
        """Create notifications for the target user and tenant admins."""
        try:
            # Notify the target user
            self.notifications.create_notification(
                user_id=target_user_id,
                tenant_id=tenant_id,
                title=title,
                message=message,
                type="INFO",
                category="AUTH",
                entity_type="User",
                entity_id=str(target_user_id),
            )
            # Notify tenant admins (except the actor)
            admins = self.repo.list_users(tenant_id, role=UserRole.TENANT_ADMIN)
            for admin in admins:
                if admin.id != actor_user_id and admin.id != target_user_id:
                    self.notifications.create_notification(
                        user_id=admin.id,
                        tenant_id=tenant_id,
                        title=title,
                        message=message,
                        type="INFO",
                        category="AUTH",
                        entity_type="User",
                        entity_id=str(target_user_id),
                    )
        except Exception as exc:
            logger.warning(f"Failed to create user event notification: {exc}")
