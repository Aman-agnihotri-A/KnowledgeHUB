from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.repositories.tenant import TenantRepository


class TenantService:
    def __init__(
        self,
        repository: TenantRepository | None = None,
    ) -> None:
        self.repository = repository or TenantRepository()

    def create_tenant(
        self,
        db: Session,
        *,
        name: str,
        slug: str,
    ) -> Tenant:
        existing_tenant = self.repository.get_by_slug(
            db,
            slug,
        )

        if existing_tenant is not None:
            raise ValueError(
                f"Tenant with slug '{slug}' already exists."
            )

        return self.repository.create(
            db,
            name=name,
            slug=slug,
        )

    def get_tenant(
        self,
        db: Session,
        tenant_id: UUID,
    ) -> Tenant | None:
        return self.repository.get_by_id(
            db,
            tenant_id,
        )

    def get_tenant_by_slug(
        self,
        db: Session,
        slug: str,
    ) -> Tenant | None:
        return self.repository.get_by_slug(
            db,
            slug,
        )

    def list_active_tenants(
        self,
        db: Session,
    ) -> list[Tenant]:
        return self.repository.list_active(db)