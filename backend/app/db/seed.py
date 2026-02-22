"""Database seed script — creates default tenant, admin user, and pipeline stages."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models.models import PipelineStage, Tenant, User, UserRole


DEFAULT_STAGES = [
    ("Lead", 0, "#6366f1", False, False),
    ("Qualified", 1, "#8b5cf6", False, False),
    ("Proposal", 2, "#a855f7", False, False),
    ("Negotiation", 3, "#d946ef", False, False),
    ("Won", 4, "#22c55e", True, False),
    ("Lost", 5, "#ef4444", False, True),
]


async def seed():
    async with async_session_factory() as db:
        # Check if default tenant exists
        result = await db.execute(select(Tenant).where(Tenant.slug == "default"))
        tenant = result.scalar_one_or_none()

        if tenant:
            print("⚡ Default tenant already exists, skipping seed.")
            return

        # Create default tenant
        tenant = Tenant(
            name="Default Organization",
            slug="default",
            settings={
                "theme": {"primary_color": "#6366f1", "logo_url": None},
                "terminology": {"deal": "Deal", "contact": "Contact", "pipeline": "Pipeline"},
            },
        )
        db.add(tenant)
        await db.flush()
        print(f"✅ Created tenant: {tenant.name} ({tenant.id})")

        # Create admin user
        admin = User(
            tenant_id=tenant.id,
            email="admin@example.com",
            hashed_password=hash_password("admin123!"),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
        )
        db.add(admin)
        print(f"✅ Created admin user: admin@example.com / admin123!")

        # Create pipeline stages
        for name, order, color, is_won, is_lost in DEFAULT_STAGES:
            db.add(PipelineStage(
                tenant_id=tenant.id, name=name, order=order,
                color=color, is_won=is_won, is_lost=is_lost,
            ))
        print("✅ Created default pipeline stages")

        await db.commit()
        print("\n🚀 Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
