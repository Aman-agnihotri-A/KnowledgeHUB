from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Tenant


class TenantRepository:
    def create(
        self,
        db: Session,
        *,
        name: str,
        slug: str,
    ) -> Tenant:
        tenant = Tenant(
            name=name,
            slug=slug,
        )

        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        return tenant

    def get_by_id(
        self,
        db: Session,
        tenant_id: UUID,
    ) -> Tenant | None:
        statement = select(Tenant).where(
            Tenant.id == tenant_id
        )

        return db.scalar(statement)

    def get_by_slug(
        self,
        db: Session,
        slug: str,
    ) -> Tenant | None:
        statement = select(Tenant).where(
            Tenant.slug == slug
        )

        return db.scalar(statement)

    def list_active(
        self,
        db: Session,
    ) -> list[Tenant]:
        statement = (
            select(Tenant)
            .where(Tenant.is_active.is_(True))
            .order_by(Tenant.name)
        )

        return list(db.scalars(statement).all())