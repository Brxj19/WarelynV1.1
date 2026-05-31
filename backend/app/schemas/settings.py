from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.currency import validate_currency_code


class TenantSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    company_display_name: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    timezone: str = "UTC"
    currency: str = "USD"
    tax_id: str | None = None
    low_stock_alert_enabled: bool = True
    over_receive_tolerance: str | None = None
    document_logo_url: str | None = None
    document_footer: str | None = None
    preferred_invoice_template_id: int | None = None
    preferred_bill_template_id: int | None = None
    preferred_invoice_email_template_id: int | None = None
    preferred_bill_email_template_id: int | None = None
    preferred_verification_template_id: int | None = None
    created_at: datetime
    updated_at: datetime


class TenantSettingsUpdate(BaseModel):
    company_display_name: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    timezone: str | None = None
    currency: str | None = None
    tax_id: str | None = None
    low_stock_alert_enabled: bool | None = None
    over_receive_tolerance: str | None = None
    document_logo_url: str | None = None
    document_footer: str | None = None
    preferred_invoice_template_id: int | None = None
    preferred_bill_template_id: int | None = None
    preferred_invoice_email_template_id: int | None = None
    preferred_bill_email_template_id: int | None = None
    preferred_verification_template_id: int | None = None

    @field_validator("currency")
    @classmethod
    def currency_must_be_supported(cls, v: str | None) -> str | None:
        if v is not None and not validate_currency_code(v):
            raise ValueError(f"Unsupported currency code '{v}'. Use a valid ISO 4217 code from the supported list.")
        return v.upper() if v else v


class UserPreferencesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    default_landing_page: str = "/dashboard"
    table_density: str = "comfortable"
    theme_preference: str = "light"
    notification_email_enabled: bool = True
    notification_in_app_enabled: bool = True
    preferred_invoice_template_id: int | None = None
    preferred_bill_template_id: int | None = None
    preferred_invoice_email_template_id: int | None = None
    preferred_bill_email_template_id: int | None = None
    preferred_verification_template_id: int | None = None
    created_at: datetime
    updated_at: datetime


class UserPreferencesUpdate(BaseModel):
    default_landing_page: str | None = None
    table_density: str | None = None
    theme_preference: str | None = None
    notification_email_enabled: bool | None = None
    notification_in_app_enabled: bool | None = None
    preferred_invoice_template_id: int | None = None
    preferred_bill_template_id: int | None = None
    preferred_invoice_email_template_id: int | None = None
    preferred_bill_email_template_id: int | None = None
    preferred_verification_template_id: int | None = None
