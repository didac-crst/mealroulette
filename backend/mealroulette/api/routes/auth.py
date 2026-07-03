from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import get_current_user
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.user import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserPublic,
)
from mealroulette.services.auth import AuthService, UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
def issue_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """OAuth2 password flow for Swagger UI Authorize (username + password)."""
    service = AuthService(db)
    user = service.authenticate(form_data.username, form_data.password)
    access_token, refresh_token = service.issue_tokens(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """JSON login for the web app. Swagger users should prefer Authorize or POST /auth/token."""
    service = AuthService(db)
    user = service.authenticate(payload.username, payload.password)
    access_token, refresh_token = service.issue_tokens(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Exchange a refresh_token from /login for a new token pair. Do not send the access_token here."""
    service = AuthService(db)
    access_token, refresh_token = service.refresh(payload.refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=204)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> None:
    AuthService(db).logout(payload.refresh_token)


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    """Return the current user. Requires Authorization: Bearer <access_token> from /login."""
    return UserService.to_public(current_user)
