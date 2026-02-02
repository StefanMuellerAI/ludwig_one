#!/usr/bin/env python3
"""
Seed default admin user into database
Run this after database initialization: python scripts/seed_admin_user.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import async_session_maker, init_db
from app.models.user import User
from app.auth.utils import get_password_hash


async def seed_admin():
    """Create default admin user if not exists"""
    print("Seeding admin user...")

    async with async_session_maker() as db:
        # Check if admin exists
        result = await db.execute(
            select(User).where(User.username == "admin")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("Admin user already exists. Skipping.")
            return

        # Create admin user
        admin = User(
            username="admin",
            email="admin@ludwigone.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_admin=True
        )

        db.add(admin)
        await db.commit()

        print("✓ Admin user created successfully")
        print("  Username: admin")
        print("  Password: admin123")
        print("  Email: admin@ludwigone.com")


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
