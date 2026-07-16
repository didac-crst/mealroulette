import argparse
import getpass
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from mealroulette.auth.security import hash_password
from mealroulette.core.config import settings
from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID, DEFAULT_HOUSEHOLD_NAME, Household
from mealroulette.models.user import User, UserRole
from mealroulette.services.household import HouseholdService


def bootstrap_admin(username: str, email: str, password: str) -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    with Session(engine) as db:
        existing = db.scalar(select(User).where(User.username == username))
        if existing is not None:
            print(f"Admin user '{username}' already exists.", file=sys.stderr)
            sys.exit(1)

        if db.get(Household, DEFAULT_HOUSEHOLD_ID) is None:
            db.add(Household(id=DEFAULT_HOUSEHOLD_ID, name=DEFAULT_HOUSEHOLD_NAME))
            db.flush()

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.admin,
            active=True,
        )
        db.add(user)
        db.flush()
        HouseholdService(db).provision_user_tenancy(user, legacy_role=UserRole.admin)
        db.commit()
        print(f"Created admin user '{username}'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the initial MealRoulette admin user.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--password",
        help="Admin password. If omitted, you will be prompted securely.",
    )
    args = parser.parse_args()

    password = args.password
    if password is None:
        password = getpass.getpass("Admin password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    bootstrap_admin(args.username, args.email, password)


if __name__ == "__main__":
    main()
