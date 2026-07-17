from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import get_current_user
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.user import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TelegramOtpRequest,
    TelegramOtpVerifyRequest,
    TokenResponse,
    UserPublic,
)
from mealroulette.schemas.household import RegisterRequest, RegisterWithInvitationRequest
from mealroulette.services.auth import AuthService, UserService
from mealroulette.services.household_membership import HouseholdMembershipService
from mealroulette.services.telegram_otp import TelegramOtpService

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


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = HouseholdMembershipService(db).register_new_household(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        household_name=payload.household_name,
    )
    access_token, refresh_token = AuthService(db).issue_tokens(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/register-with-invitation", response_model=TokenResponse, status_code=201)
def register_with_invitation(payload: RegisterWithInvitationRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = HouseholdMembershipService(db).register_with_invitation(
        token=payload.token,
        username=payload.username,
        email=payload.email,
        password=payload.password,
    )
    access_token, refresh_token = AuthService(db).issue_tokens(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserPublic)
def me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPublic:
    """Return the current user. Requires Authorization: Bearer <access_token> from /login."""
    return UserService(db).to_public(current_user)


@router.post("/change-password", status_code=204)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    AuthService(db).change_password(
        current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )


@router.post("/telegram-otp/request", status_code=202)
def request_telegram_otp(payload: TelegramOtpRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    service = TelegramOtpService(db)
    service.request_login_code(payload.username)
    return {"detail": service.GENERIC_DETAIL}


@router.post("/telegram-otp/verify", response_model=TokenResponse)
def verify_telegram_otp(payload: TelegramOtpVerifyRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = TelegramOtpService(db).verify_login_code(payload.username, payload.code)
    access_token, refresh_token = AuthService(db).issue_tokens(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
