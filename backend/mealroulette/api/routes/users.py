from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from mealroulette.auth.dependencies import get_current_admin
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.user import UserCreateRequest, UserPublic, UserUpdateRequest
from mealroulette.services.auth import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserPublic])
def list_users(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[UserPublic]:
    service = UserService(db)
    return [service.to_public(user) for user in service.list_users()]


@router.post("", response_model=UserPublic, status_code=201)
def create_user(
    payload: UserCreateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> UserPublic:
    service = UserService(db)
    return service.to_public(service.create_user(payload))


@router.get("/{user_id}", response_model=UserPublic)
def get_user(
    user_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> UserPublic:
    service = UserService(db)
    return service.to_public(service.get_user(user_id))


@router.put("/{user_id}", response_model=UserPublic)
def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> UserPublic:
    service = UserService(db)
    return service.to_public(service.update_user(user_id, payload))


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    UserService(db).delete_user(user_id)
