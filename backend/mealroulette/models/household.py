from __future__ import annotations

import enum
from datetime import datetime, time
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from mealroulette.db.base import Base

if TYPE_CHECKING:
    from mealroulette.models.user import User

DEFAULT_HOUSEHOLD_ID = UUID("00000000-0000-4000-8000-000000000001")
DEFAULT_HOUSEHOLD_NAME = "Default household"


class HouseholdRole(str, enum.Enum):
    household_admin = "household_admin"
    household_member = "household_member"


class PlatformRole(str, enum.Enum):
    platform_admin = "platform_admin"


class Household(Base):
    __tablename__ = "households"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    memberships: Mapped[list["HouseholdMembership"]] = relationship(
        back_populates="household",
        cascade="all, delete-orphan",
    )


class HouseholdMembership(Base):
    __tablename__ = "household_memberships"
    __table_args__ = (UniqueConstraint("household_id", "user_id", name="uq_household_memberships_household_user"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    household_id: Mapped[UUID] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[HouseholdRole] = mapped_column(Enum(HouseholdRole, name="household_role"))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    household: Mapped[Household] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="household_memberships")


class HouseholdInvitation(Base):
    __tablename__ = "household_invitations"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_household_invitations_token_hash"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    household_id: Mapped[UUID] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"),
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    household: Mapped[Household] = relationship()
    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_user_id])
    accepted_by: Mapped["User | None"] = relationship(foreign_keys=[accepted_by_user_id])


class UserPlatformRole(Base):
    __tablename__ = "user_platform_roles"
    __table_args__ = (UniqueConstraint("user_id", "role", name="uq_user_platform_roles_user_role"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[PlatformRole] = mapped_column(Enum(PlatformRole, name="platform_role"))
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="platform_roles")


class HouseholdNotificationSubscription(Base):
    __tablename__ = "household_notification_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "household_id",
            name="uq_household_notification_subscriptions_user_household",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    household_id: Mapped[UUID] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    notify_daily_reminder: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_shopping: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_roulette: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    daily_reminder_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(8, 0))
    shopping_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Paris")
    last_reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
