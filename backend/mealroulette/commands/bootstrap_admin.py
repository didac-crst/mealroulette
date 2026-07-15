"""Deprecated alias — use bootstrap_platform_admin."""

import sys
import warnings

from mealroulette.commands.bootstrap_platform_admin import bootstrap_platform_admin, main as bootstrap_main


def bootstrap_admin(username: str, email: str, password: str) -> None:
    warnings.warn(
        "bootstrap_admin is deprecated; use bootstrap_platform_admin instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    bootstrap_platform_admin(username, email, password)


def main() -> None:
    print(
        "Note: bootstrap_admin now creates a platform operator without household membership. "
        "Use: python -m mealroulette.commands.bootstrap_platform_admin",
        file=sys.stderr,
    )
    bootstrap_main()


if __name__ == "__main__":
    main()
