from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import (
    get_current_household_admin,
    get_current_household_scope,
    get_current_platform_admin,
    get_current_user,
    HouseholdScope,
)
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.household import (
    AcceptInvitationRequest,
    HouseholdInvitationCreated,
    HouseholdInvitationPublic,
    HouseholdMemberPublic,
    HouseholdPublic,
    IngredientProposalCreateRequest,
    IngredientProposalPublic,
    IngredientProposalReviewRequest,
    NotificationSubscriptionPublic,
    NotificationSubscriptionUpdateRequest,
    TelegramLinkTokenPublic,
    TelegramUserLinkPublic,
    UpdateHouseholdRequest,
    UpdateMemberRoleRequest,
)
from mealroulette.schemas.telegram import TelegramSendResult
from mealroulette.services.ingredient_proposal import IngredientProposalService
from mealroulette.services.household import HouseholdService
from mealroulette.services.household_membership import HouseholdMembershipService
from mealroulette.services.telegram_link import TelegramLinkService, build_telegram_link_deep_url
from mealroulette.services.telegram_reminder import TelegramReminderService

router = APIRouter(prefix="/household", tags=["household"])


@router.get("", response_model=HouseholdPublic)
def get_current_household(
    scope: HouseholdScope = Depends(get_current_household_scope),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HouseholdPublic:
    household = HouseholdService(db).get_household(scope.household_id)
    return HouseholdPublic.model_validate(household)


@router.patch("", response_model=HouseholdPublic)
def update_current_household(
    payload: UpdateHouseholdRequest,
    scope: HouseholdScope = Depends(get_current_household_scope),
    _admin: User = Depends(get_current_household_admin),
    db: Session = Depends(get_db),
) -> HouseholdPublic:
    household = HouseholdService(db).rename_household(scope.household_id, payload.name)
    return HouseholdPublic.model_validate(household)


@router.get("/members", response_model=list[HouseholdMemberPublic])
def list_household_members(
    scope: HouseholdScope = Depends(get_current_household_scope),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[HouseholdMemberPublic]:
    service = HouseholdMembershipService(db)
    members = service.list_members(scope.household_id)
    return [
        HouseholdMemberPublic(
            membership_id=membership.id,
            user_id=membership.user_id,
            username=membership.user.username,
            email=membership.user.email,
            role=membership.role,
            joined_at=membership.joined_at,
        )
        for membership in members
    ]


@router.patch("/members/{membership_id}", response_model=HouseholdMemberPublic)
def update_household_member_role(
    membership_id: UUID,
    payload: UpdateMemberRoleRequest,
    scope: HouseholdScope = Depends(get_current_household_scope),
    _admin: User = Depends(get_current_household_admin),
    db: Session = Depends(get_db),
) -> HouseholdMemberPublic:
    service = HouseholdMembershipService(db)
    membership = service.update_member_role(membership_id, scope.household_id, payload.role)
    return HouseholdMemberPublic(
        membership_id=membership.id,
        user_id=membership.user_id,
        username=membership.user.username,
        email=membership.user.email,
        role=membership.role,
        joined_at=membership.joined_at,
    )


@router.delete("/members/{membership_id}", status_code=204)
def remove_household_member(
    membership_id: UUID,
    scope: HouseholdScope = Depends(get_current_household_scope),
    _admin: User = Depends(get_current_household_admin),
    db: Session = Depends(get_db),
) -> None:
    HouseholdMembershipService(db).remove_member(membership_id, scope.household_id)


@router.post("/invitations", response_model=HouseholdInvitationCreated, status_code=201)
def create_household_invitation(
    scope: HouseholdScope = Depends(get_current_household_scope),
    admin: User = Depends(get_current_household_admin),
    db: Session = Depends(get_db),
) -> HouseholdInvitationCreated:
    service = HouseholdMembershipService(db)
    invitation, token = service.create_invitation(scope.household_id, admin.id)
    return HouseholdInvitationCreated(
        invitation=HouseholdInvitationPublic.model_validate(invitation),
        invite_url=f"/join?token={token}",
    )


@router.get("/invitations", response_model=list[HouseholdInvitationPublic])
def list_household_invitations(
    scope: HouseholdScope = Depends(get_current_household_scope),
    _admin: User = Depends(get_current_household_admin),
    db: Session = Depends(get_db),
) -> list[HouseholdInvitationPublic]:
    invitations = HouseholdMembershipService(db).list_invitations(scope.household_id)
    return [HouseholdInvitationPublic.model_validate(row) for row in invitations]


@router.delete("/invitations/{invitation_id}", status_code=204)
def revoke_household_invitation(
    invitation_id: UUID,
    scope: HouseholdScope = Depends(get_current_household_scope),
    _admin: User = Depends(get_current_household_admin),
    db: Session = Depends(get_db),
) -> None:
    HouseholdMembershipService(db).revoke_invitation(invitation_id, scope.household_id)


@router.post("/invitations/accept", status_code=204)
def accept_household_invitation(
    payload: AcceptInvitationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    HouseholdMembershipService(db).accept_invitation_for_user(payload.token, current_user)


@router.post("/ingredient-proposals", response_model=IngredientProposalPublic, status_code=201)
def create_ingredient_proposal(
    payload: IngredientProposalCreateRequest,
    scope: HouseholdScope = Depends(get_current_household_scope),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IngredientProposalPublic:
    proposal = IngredientProposalService(db).create_proposal(
        household_id=scope.household_id,
        user=user,
        proposed_name=payload.proposed_name,
        reason=payload.reason,
    )
    return IngredientProposalPublic.model_validate(proposal)


@router.get("/ingredient-proposals", response_model=list[IngredientProposalPublic])
def list_household_ingredient_proposals(
    scope: HouseholdScope = Depends(get_current_household_scope),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[IngredientProposalPublic]:
    rows = IngredientProposalService(db).list_for_household(scope.household_id)
    return [IngredientProposalPublic.model_validate(row) for row in rows]


@router.get("/platform/ingredient-proposals", response_model=list[IngredientProposalPublic])
def list_pending_ingredient_proposals(
    _admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> list[IngredientProposalPublic]:
    rows = IngredientProposalService(db).list_pending()
    return [IngredientProposalPublic.model_validate(row) for row in rows]


@router.post("/platform/ingredient-proposals/{proposal_id}/review", response_model=IngredientProposalPublic)
def review_ingredient_proposal(
    proposal_id: UUID,
    payload: IngredientProposalReviewRequest,
    admin: User = Depends(get_current_platform_admin),
    db: Session = Depends(get_db),
) -> IngredientProposalPublic:
    row = IngredientProposalService(db).review(
        proposal_id,
        reviewer=admin,
        approve=payload.approve,
        review_note=payload.review_note,
    )
    return IngredientProposalPublic.model_validate(row)


@router.post("/telegram/link-token", response_model=TelegramLinkTokenPublic)
def create_telegram_link_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TelegramLinkTokenPublic:
    row, token = TelegramLinkService(db).create_link_token(current_user.id)
    return TelegramLinkTokenPublic(
        token=token,
        expires_at=row.expires_at,
        deep_link_url=build_telegram_link_deep_url(token),
    )


@router.get("/telegram/link", response_model=TelegramUserLinkPublic)
def get_telegram_link(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TelegramUserLinkPublic:
    link = TelegramLinkService(db).get_link_for_user(current_user.id)
    if link is None:
        return TelegramUserLinkPublic(linked=False)
    return TelegramUserLinkPublic(
        linked=True,
        username=link.username,
        display_name=link.display_name,
        linked_at=link.linked_at,
    )


@router.delete("/telegram/link", status_code=204)
def unlink_telegram(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    TelegramLinkService(db).unlink_user(current_user.id)


def _subscription_public(row) -> NotificationSubscriptionPublic:
    return NotificationSubscriptionPublic(
        notify_daily_reminder=row.notify_daily_reminder,
        notify_shopping=row.notify_shopping,
        notify_roulette=row.notify_roulette,
        daily_reminder_time=row.daily_reminder_time,
        shopping_window_days=row.shopping_window_days,
        timezone=row.timezone,
        last_reminder_sent_at=row.last_reminder_sent_at,
    )


@router.get("/notification-subscription", response_model=NotificationSubscriptionPublic)
def get_notification_subscription(
    scope: HouseholdScope = Depends(get_current_household_scope),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationSubscriptionPublic:
    row = HouseholdMembershipService(db).ensure_notification_subscription(current_user.id, scope.household_id)
    return _subscription_public(row)


@router.put("/notification-subscription", response_model=NotificationSubscriptionPublic)
def update_notification_subscription(
    payload: NotificationSubscriptionUpdateRequest,
    scope: HouseholdScope = Depends(get_current_household_scope),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationSubscriptionPublic:
    row = HouseholdMembershipService(db).ensure_notification_subscription(current_user.id, scope.household_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return _subscription_public(row)


@router.post("/telegram/test", response_model=TelegramSendResult)
def send_personal_telegram_test(
    scope: HouseholdScope = Depends(get_current_household_scope),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TelegramSendResult:
    return TelegramReminderService(db).send_personal_test_message(current_user.id, scope.household_id)


@router.post("/telegram/send-daily-reminder", response_model=TelegramSendResult)
def send_personal_daily_reminder(
    scope: HouseholdScope = Depends(get_current_household_scope),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TelegramSendResult:
    return TelegramReminderService(db).send_personal_daily_reminder(current_user.id, scope.household_id)
