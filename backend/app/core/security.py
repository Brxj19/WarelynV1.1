from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

import jwt
import bcrypt

from app.core.config import get_settings
from app.core.exceptions import AppError


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str, claims: dict[str, object] | None = None) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, object] = {
        "sub": subject,
        "type": "access",
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": str(uuid4()),
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_token(token: str, expected_type: str) -> dict[str, object]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise AppError("EXPIRED_TOKEN", "Token has expired.", 401) from exc
    except jwt.PyJWTError as exc:
        raise AppError("INVALID_TOKEN", "Token is invalid.", 401) from exc

    if payload.get("type") != expected_type:
        raise AppError("INVALID_TOKEN", "Token type is invalid.", 401)
    return payload


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
