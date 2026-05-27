from fastapi import APIRouter, Depends, Request, Response, status
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
