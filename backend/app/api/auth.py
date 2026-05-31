from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.limiter import limiter
from app.db.session import get_db
from app.dependencies.auth import get_current_user_context
from app.schemas.auth import (
    AuthMeResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RegisterRequest,
    RegisterResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
)
from app.services.auth import AuthService, UserContext

router = APIRouter(prefix="/auth", tags=["auth"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=1, max_length=12)


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    return AuthService(db).register_tenant_admin(payload)


@router.post("/login", response_model=LoginResponse)
@limiter.limit("15/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    return AuthService(db).login(str(payload.email), payload.password)


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh_token(request: TokenRefreshRequest, db: Session = Depends(get_db)) -> TokenRefreshResponse:
    return AuthService(db).refresh_access_token(request.refresh_token)


@router.get("/me", response_model=AuthMeResponse)
def me(context: UserContext = Depends(get_current_user_context)) -> AuthMeResponse:
    return AuthMeResponse(user=context.user, tenant=context.tenant, role=context.role)


@router.post("/logout", response_model=LogoutResponse)
def logout(request: TokenRefreshRequest | None = None, db: Session = Depends(get_db)) -> LogoutResponse:
    AuthService(db).logout(request.refresh_token if request else None)
    return LogoutResponse(success=True)


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def forgot_password(request: Request, payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> None:
    AuthService(db).request_password_reset(str(payload.email))


@router.post("/verify-reset-code")
@limiter.limit("20/minute")
def verify_reset_code(request: Request, payload: VerifyResetCodeRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    reset_token = AuthService(db).verify_reset_code(str(payload.email), payload.code.strip())
    return {"reset_token": reset_token}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> None:
    AuthService(db).reset_password(payload.reset_token, payload.new_password)
