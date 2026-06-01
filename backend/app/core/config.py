from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ENV_FILE,
        env_prefix="WARELYN_",
        case_sensitive=False,
    )

    app_name: str = "Warelyn Inventory API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api"

    database_url: str
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 300000
    refresh_token_expire_days: int = 14

    super_admin_email: str
    super_admin_password: str
    super_admin_name: str = "Warelyn Super Admin"
    seed_super_admin_on_startup: bool = True

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "no-reply@warelyn.local"
    smtp_from_name: str = "Warelyn"
    smtp_use_tls: bool = False
    smtp_use_ssl: bool = False
    email_delivery_mode: str = "mailhog"

    otp_code_length: int = 6
    otp_expire_minutes: int = 10
    otp_max_attempts: int = 5

    gemini_api_key: str
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    ai_retrieval_candidates: int = 32
    ai_retrieval_top_k: int = 6
    ai_min_confidence: float = 0.42

    @field_validator("database_url", "jwt_secret_key", "super_admin_email", "super_admin_password", "gemini_api_key")
    @classmethod
    def required_secret_setting(cls, value: str, info):
        if not value or not value.strip():
            raise ValueError(f"WARELYN_{info.field_name.upper()} must be set in the environment")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
