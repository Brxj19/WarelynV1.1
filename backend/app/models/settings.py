from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TenantSettings(Base):
    __tablename__ = "tenant_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    company_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    low_stock_alert_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    over_receive_tolerance: Mapped[str | None] = mapped_column(String(20), nullable=True)
    document_logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    document_footer: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_invoice_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    preferred_bill_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    preferred_invoice_email_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    preferred_bill_email_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    preferred_verification_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    default_landing_page: Mapped[str] = mapped_column(String(120), default="/dashboard", nullable=False)
    table_density: Mapped[str] = mapped_column(String(20), default="comfortable", nullable=False)
    theme_preference: Mapped[str] = mapped_column(String(20), default="light", nullable=False)
    notification_email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notification_in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    preferred_invoice_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    preferred_bill_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    preferred_invoice_email_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    preferred_bill_email_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    preferred_verification_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
