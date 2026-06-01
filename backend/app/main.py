from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.limiter import limiter
from app.core.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from app.db.session import SessionLocal
from app.services.assistant import AssistantService
from app.services.auth import AuthService


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    import os
    alembic_cfg = AlembicConfig(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic"))
    command.upgrade(alembic_cfg, "head")

    if settings.seed_super_admin_on_startup:
        db = SessionLocal()
        try:
            AuthService(db).ensure_super_admin(
                email=settings.super_admin_email,
                password=settings.super_admin_password,
                name=settings.super_admin_name,
            )
        except SQLAlchemyError:
            db.rollback()
            raise
        finally:
            db.close()
    if settings.gemini_api_key:
        db = SessionLocal()
        try:
            AssistantService(db).ensure_bootstrap_index()
        except Exception:
            db.rollback()
        finally:
            db.close()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    if not settings.debug:
        if "*" in str(settings.cors_origins):
            raise RuntimeError("CORS wildcard (*) is not allowed in production. Set WARELYN_CORS_ORIGINS to your frontend domain.")
        if settings.jwt_secret_key in ("replace-with-a-long-random-secret", "change-this-dev-secret-before-production", "changeme", ""):
            raise RuntimeError("JWT_SECRET_KEY must be changed from its default value before production deployment.")

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    import os
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

    return app


app = create_app()
