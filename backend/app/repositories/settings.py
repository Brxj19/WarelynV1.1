from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.settings import TenantSettings, UserPreferences


class TenantSettingsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_tenant(self, tenant_id: int) -> TenantSettings | None:
        return self.db.scalar(select(TenantSettings).where(TenantSettings.tenant_id == tenant_id))

    def get_or_create(self, tenant_id: int) -> TenantSettings:
        settings = self.get_by_tenant(tenant_id)
        if settings is not None:
            return settings
        settings = TenantSettings(tenant_id=tenant_id)
        self.db.add(settings)
        self.db.flush()
        return settings

    def update(self, tenant_id: int, values: dict[str, Any]) -> TenantSettings | None:
        settings = self.get_by_tenant(tenant_id)
        if settings is None:
            return None
        for key, value in values.items():
            setattr(settings, key, value)
        self.db.flush()
        return settings


class UserPreferencesRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user(self, user_id: int) -> UserPreferences | None:
        return self.db.scalar(select(UserPreferences).where(UserPreferences.user_id == user_id))

    def get_or_create(self, user_id: int) -> UserPreferences:
        prefs = self.get_by_user(user_id)
        if prefs is not None:
            return prefs
        prefs = UserPreferences(user_id=user_id)
        self.db.add(prefs)
        self.db.flush()
        return prefs

    def update(self, user_id: int, values: dict[str, Any]) -> UserPreferences | None:
        prefs = self.get_by_user(user_id)
        if prefs is None:
            return None
        for key, value in values.items():
            setattr(prefs, key, value)
        self.db.flush()
        return prefs
