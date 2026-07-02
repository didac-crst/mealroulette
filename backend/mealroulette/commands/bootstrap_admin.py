import argparse
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from mealroulette.auth.security import hash_password
from mealroulette.core.config import settings
from mealroulette.models.user import User, UserRole


def bootstrap_admin(username: str, email: str, password: str) -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    with Session(engine) as db:
        existing = db.scalar(select(User).where(User.username == username))
        if existing is not None:
            print(f"Admin user '{username}' already exists.", file=sys.stderr)
            sys.exit(1)

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.admin,
            active=True,
        )
        db.add(user)
        db.commit()
        print(f"Created admin user '{username}'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the initial MealRoulette admin user.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    bootstrap_admin(args.username, args.email, args.password)


if __name__ == "__main__":
    main()
