from unittest.mock import MagicMock
from uuid import uuid4

from app.models.tenant import Tenant
from app.repositories.tenant import TenantRepository


def test_create_tenant():
    db = MagicMock()
    repository = TenantRepository()

    tenant = repository.create(
        db,
        name="Acme Corporation",
        slug="acme",
    )

    assert tenant.name == "Acme Corporation"
    assert tenant.slug == "acme"

    db.add.assert_called_once_with(tenant)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(tenant)


def test_get_tenant_by_id():
    db = MagicMock()
    repository = TenantRepository()

    tenant_id = uuid4()
    tenant = Tenant(
        name="Acme Corporation",
        slug="acme",
    )

    db.scalar.return_value = tenant

    result = repository.get_by_id(
        db,
        tenant_id,
    )

    assert result is tenant
    db.scalar.assert_called_once()


def test_get_tenant_by_slug():
    db = MagicMock()
    repository = TenantRepository()

    tenant = Tenant(
        name="Acme Corporation",
        slug="acme",
    )

    db.scalar.return_value = tenant

    result = repository.get_by_slug(
        db,
        "acme",
    )

    assert result is tenant
    db.scalar.assert_called_once()


def test_list_active_tenants():
    db = MagicMock()
    repository = TenantRepository()

    tenant = Tenant(
        name="Acme Corporation",
        slug="acme",
    )

    db.scalars.return_value.all.return_value = [tenant]

    result = repository.list_active(db)

    assert result == [tenant]