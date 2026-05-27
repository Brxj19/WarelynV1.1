import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.documents import DocumentTemplatePurpose
from app.repositories.audit import AuditLogRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.settings import TenantSettingsRepository, UserPreferencesRepository

# Preference field -> expected purpose
_PREFERENCE_PURPOSE_MAP: dict[str, DocumentTemplatePurpose] = {
    "preferred_invoice_template_id": DocumentTemplatePurpose.INVOICE_PDF,
    "preferred_bill_template_id": DocumentTemplatePurpose.BILL_PDF,
    "preferred_invoice_email_template_id": DocumentTemplatePurpose.INVOICE_EMAIL,
    "preferred_bill_email_template_id": DocumentTemplatePurpose.BILL_EMAIL,
    "preferred_verification_template_id": DocumentTemplatePurpose.EMAIL_VERIFICATION,
}


class TenantSettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = TenantSettingsRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def get_settings(self, tenant_id: int) -> Any:
        settings = self.repository.get_or_create(tenant_id)
        self.db.commit()
        return settings

    def update_settings(self, tenant_id: int, values: dict[str, Any], actor_user_id: int | None = None, actor_role: str = "") -> Any:
        self.repository.get_or_create(tenant_id)
        result = self.repository.update(tenant_id, values)
        if result is None:
            raise AppError("SETTINGS_NOT_FOUND", "Tenant settings were not found.", 404)
        self.audit_logs.create(
            {
                "tenant_id": tenant_id,
                "actor_user_id": actor_user_id,
                "actor_role": actor_role,
                "action": "SETTINGS_UPDATE",
                "entity_type": "tenant_settings",
                "entity_id": str(tenant_id),
                "metadata_json": json.dumps({"updated_fields": list(values.keys())}, default=str),
            }
        )
        self.db.commit()
        self.db.refresh(result)
        return result


class UserPreferencesService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = UserPreferencesRepository(db)
        self.audit_logs = AuditLogRepository(db)
        self.docs_repository = DocumentsRepository(db)

    def get_preferences(self, user_id: int) -> Any:
        prefs = self.repository.get_or_create(user_id)
        self.db.commit()
        return prefs

    def update_preferences(self, user_id: int, values: dict[str, Any], actor_role: str = "", tenant_id: int | None = None) -> Any:
        # Validate template preferences if any are being set
        for field, expected_purpose in _PREFERENCE_PURPOSE_MAP.items():
            if field in values and values[field] is not None:
                template_id = values[field]
                if tenant_id is None:
                    raise AppError(
                        "TEMPLATE_VALIDATION_FAILED",
                        "Tenant context is required to validate template preferences.",
                        400,
                    )
                template = self.docs_repository.get_template(tenant_id, template_id)
                if template is None:
                    raise AppError(
                        "DOCUMENT_TEMPLATE_NOT_FOUND",
                        f"Template {template_id} not found or does not belong to this tenant.",
                        400,
                    )
                if not template.is_active:
                    raise AppError(
                        "TEMPLATE_INACTIVE",
                        f"Cannot set inactive template as preference for {field}.",
                        400,
                    )
                if template.purpose != expected_purpose:
                    raise AppError(
                        "TEMPLATE_PURPOSE_MISMATCH",
                        f"Template purpose '{template.purpose.value}' does not match expected purpose '{expected_purpose.value}' for {field}.",
                        400,
                    )

        self.repository.get_or_create(user_id)
        result = self.repository.update(user_id, values)
        if result is None:
            raise AppError("PREFERENCES_NOT_FOUND", "User preferences were not found.", 404)
        self.audit_logs.create(
            {
                "tenant_id": None,
                "actor_user_id": user_id,
                "actor_role": actor_role,
                "action": "PREFERENCES_UPDATE",
                "entity_type": "user_preferences",
                "entity_id": str(user_id),
                "metadata_json": json.dumps({"updated_fields": list(values.keys())}, default=str),
            }
        )
        self.db.commit()
        self.db.refresh(result)
        return result
