import argparse
import getpass
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from mealroulette.auth.security import hash_password
from mealroulette.core.config import settings
from mealroulette.models.user import User, UserRole
from mealroulette.services.household import HouseholdService


def bootstrap_platform_admin(username: str, email: str, password: str) -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    with Session(engine) as db:
        existing = db.scalar(select(User).where(User.username == username))
        if existing is not None:
            print(f"Platform admin '{username}' already exists.", file=sys.stderr)
            sys.exit(1)

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.user,
            active=True,
        )
        db.add(user)
        db.flush()
        HouseholdService(db).provision_platform_admin(user)
        db.commit()
        print(f"Created platform admin '{username}' (no household membership).")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a MealRoulette platform operator (platform_admin, no household)."
    )
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--password",
        help="Password. If omitted, you will be prompted securely.",
    )
    args = parser.parse_args()

    password = args.password
    if password is None:
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    bootstrap_platform_admin(args.username, args.email, password)


if __name__ == "__main__":
    main()
