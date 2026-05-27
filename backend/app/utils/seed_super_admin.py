from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.auth import AuthService


def main() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        AuthService(db).ensure_super_admin(
            email=settings.super_admin_email,
            password=settings.super_admin_password,
            name=settings.super_admin_name,
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
