from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="WARELYN_",
        case_sensitive=False,
    )

    app_name: str = "Warelyn Inventory API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api"

    database_url: str = "mysql+pymysql://warelyn:warelyn_dev_password@localhost:3306/warelyn_inventoryV1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])

    jwt_secret_key: str = "change-this-dev-secret-before-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 300000
    refresh_token_expire_days: int = 14

    super_admin_email: str = "admin@warelyn.dev"
    super_admin_password: str = "ChangeMe123!"
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

    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_chat_model: str = "gemini-1.5-flash"
    gemini_embedding_model: str = "text-embedding-004"
    ai_retrieval_candidates: int = 24
    ai_retrieval_top_k: int = 6
    ai_min_confidence: float = 0.42


@lru_cache
def get_settings() -> Settings:
    return Settings()
