#!/usr/bin/env python3
"""
Seed default admin user into database
Run this after database initialization: python scripts/seed_admin_user.py
"""
import asyncio
import sys
from pathlib import Path
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import async_session_maker, init_db
from app.models.user import User
from app.auth.utils import get_password_hash


async def seed_admin():
    """Create default admin user if not exists"""
    print("Seeding admin user...")

    admin_username = os.getenv("ADMIN_USERNAME")
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_username or not admin_email or not admin_password:
        raise ValueError(
            "ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD must be set to seed an admin user."
        )

    async with async_session_maker() as db:
        # Check if admin exists
        result = await db.execute(
            select(User).where(User.username == admin_username)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("Admin user already exists. Skipping.")
            return

        # Create admin user
        admin = User(
            username=admin_username,
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            is_active=True,
            is_admin=True,
            must_change_password=True
        )

        db.add(admin)
        await db.commit()

        print("✓ Admin user created successfully")
        print(f"  Username: {admin_username}")
        print("  Password: [set via ADMIN_PASSWORD]")
        print(f"  Email: {admin_email}")


async def main():
    """Main function"""
    try:
        print("Initializing database connection...")
        await init_db()

        await seed_admin()

        print("\n✓ Seeding completed successfully!")

    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
