"""CLI tools for Arbi backend administration.

Usage:
    uv run python -m app.cli seed
    uv run python -m app.cli promote-admin --email demo@arbi.dev
"""

import argparse
import asyncio
import sys

from sqlalchemy import select

from app.database.connection import AsyncSessionLocal
from app.seed_profiles import seed_demo


async def _seed() -> None:
    async with AsyncSessionLocal() as session:
        result = await seed_demo(session)
    if result["status"] == "already_seeded":
        print(f"Demo data already present (user_id={result['user_id']}).")  # noqa: T201
    else:
        print(f"Seeded demo data: {result['email']} (user_id={result['user_id']}, project_id={result['project_id']}).")  # noqa: T201


async def _promote_admin(email: str) -> None:
    from app.auth.models import User

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user is None:
            print(f"Error: no user found with email '{email}'", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        user.role = "admin"
        await session.commit()
        print(f"User '{email}' (id={user.id}) promoted to admin.")  # noqa: T201


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli", description="Arbi backend admin CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("seed", help="Insert the demo dataset (idempotent)")

    promote = sub.add_parser("promote-admin", help="Promote a user to admin")
    promote.add_argument("--email", required=True)

    args = parser.parse_args()
    if args.command == "seed":
        asyncio.run(_seed())
    elif args.command == "promote-admin":
        asyncio.run(_promote_admin(args.email))


if __name__ == "__main__":
    main()
