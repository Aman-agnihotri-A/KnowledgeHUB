"""Create deterministic local demo users for KnowledgeHub.

This script is intended for local development only.
It uses the application's existing service layer so passwords are
hashed exactly the same way as normal user creation.
"""
from __future__ import annotations

from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.services.tenant import TenantService
from app.services.user import UserService


DEMO_TENANT_NAME = os.getenv(
    "KH_DEMO_TENANT_NAME",
    "KnowledgeHub Demo",
)
DEMO_TENANT_SLUG = os.getenv(
    "KH_DEMO_TENANT_SLUG",
    "knowledgehub-demo",
)

SUPER_ADMIN_EMAIL = os.getenv(
    "KH_DEMO_SUPER_ADMIN_EMAIL",
    "superadmin@knowledgehub.local",
)
SUPER_ADMIN_PASSWORD = os.getenv(
    "KH_DEMO_SUPER_ADMIN_PASSWORD",
    "SuperAdmin@123",
)

TENANT_ADMIN_EMAIL = os.getenv(
    "KH_DEMO_TENANT_ADMIN_EMAIL",
    "admin@knowledgehub.local",
)
TENANT_ADMIN_PASSWORD = os.getenv(
    "KH_DEMO_TENANT_ADMIN_PASSWORD",
    "TenantAdmin@123",
)

SUB_USER_EMAIL = os.getenv(
    "KH_DEMO_SUB_USER_EMAIL",
    "user@knowledgehub.local",
)
SUB_USER_PASSWORD = os.getenv(
    "KH_DEMO_SUB_USER_PASSWORD",
    "SubUser@123",
)


def get_or_create_tenant(
    tenant_service: TenantService,
    db,
):
    tenant = tenant_service.get_tenant_by_slug(
        db,
        DEMO_TENANT_SLUG,
    )

    if tenant is not None:
        return tenant

    return tenant_service.create_tenant(
        db,
        name=DEMO_TENANT_NAME,
        slug=DEMO_TENANT_SLUG,
    )


def get_or_create_user(
    user_service: UserService,
    db,
    *,
    email: str,
    password: str,
    full_name: str,
    role: UserRole,
    tenant_id=None,
):
    user = user_service.get_user_by_email(
        db,
        email,
    )

    if user is not None:
        if user.role != role:
            raise RuntimeError(
                f"Existing user '{email}' has role "
                f"'{user.role.value}', expected '{role.value}'."
            )

        if user.tenant_id != tenant_id:
            raise RuntimeError(
                f"Existing user '{email}' belongs to a different tenant."
            )

        if not user.is_active:
            user.is_active = True
            db.commit()
            db.refresh(user)

        return user

    return user_service.create_user(
        db,
        email=email,
        password=password,
        full_name=full_name,
        role=role,
        tenant_id=tenant_id,
    )


def main() -> None:
    db = SessionLocal()

    tenant_service = TenantService()
    user_service = UserService()

    try:
        tenant = get_or_create_tenant(
            tenant_service,
            db,
        )

        super_admin = get_or_create_user(
            user_service,
            db,
            email=SUPER_ADMIN_EMAIL,
            password=SUPER_ADMIN_PASSWORD,
            full_name="KnowledgeHub Super Admin",
            role=UserRole.SUPER_ADMIN,
            tenant_id=None,
        )

        tenant_admin = get_or_create_user(
            user_service,
            db,
            email=TENANT_ADMIN_EMAIL,
            password=TENANT_ADMIN_PASSWORD,
            full_name="KnowledgeHub Tenant Admin",
            role=UserRole.TENANT_ADMIN,
            tenant_id=tenant.id,
        )

        sub_user = get_or_create_user(
            user_service,
            db,
            email=SUB_USER_EMAIL,
            password=SUB_USER_PASSWORD,
            full_name="KnowledgeHub Demo User",
            role=UserRole.SUB_USER,
            tenant_id=tenant.id,
        )

        print()
        print("KnowledgeHub local demo data is ready.")
        print()
        print(f"Tenant:       {tenant.name}")
        print(f"Tenant slug:  {tenant.slug}")
        print(f"Tenant ID:    {tenant.id}")
        print()
        print("Super Admin")
        print(f"  Email:      {super_admin.email}")
        print(f"  Password:   {SUPER_ADMIN_PASSWORD}")
        print()
        print("Tenant Admin")
        print(f"  Email:      {tenant_admin.email}")
        print(f"  Password:   {TENANT_ADMIN_PASSWORD}")
        print()
        print("Sub User")
        print(f"  Email:      {sub_user.email}")
        print(f"  Password:   {SUB_USER_PASSWORD}")
        print()
        print("For KH-038 browser testing, use the Tenant Admin")
        print("or Sub User credentials.")
        print()

    finally:
        db.close()


if __name__ == "__main__":
    main()
