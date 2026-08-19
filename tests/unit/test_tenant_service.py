from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.tenant import Tenant
from app.services.tenant import TenantService


def test_create_tenant():
    db = MagicMock()
    repository = MagicMock()
    service = TenantService(repository)

    tenant = Tenant(
        name="Acme Corporation",
        slug="acme",
    )

    repository.get_by_slug.return_value = None
    repository.create.return_value = tenant

    result = service.create_tenant(
        db,
        name="Acme Corporation",
        slug="acme",
    )

    assert result is tenant

    repository.get_by_slug.assert_called_once_with(
        db,
        "acme",
    )

    repository.create.assert_called_once_with(
        db,
        name="Acme Corporation",
        slug="acme",
    )


def test_create_tenant_rejects_duplicate_slug():
    db = MagicMock()
    repository = MagicMock()
    service = TenantService(repository)

    existing_tenant = Tenant(
        name="Existing Corporation",
        slug="acme",
    )

    repository.get_by_slug.return_value = existing_tenant

    with pytest.raises(
        ValueError,
        match="Tenant with slug 'acme' already exists.",
    ):
        service.create_tenant(
            db,
            name="Another Corporation",
            slug="acme",
        )

    repository.create.assert_not_called()


def test_get_tenant():
    db = MagicMock()
    repository = MagicMock()
    service = TenantService(repository)

    tenant_id = uuid4()

    tenant = Tenant(
        name="Acme Corporation",
        slug="acme",
    )

    repository.get_by_id.return_value = tenant

    result = service.get_tenant(
        db,
        tenant_id,
    )

    assert result is tenant

    repository.get_by_id.assert_called_once_with(
        db,
        tenant_id,
    )


def test_get_tenant_by_slug():
    db = MagicMock()
    repository = MagicMock()
    service = TenantService(repository)

    tenant = Tenant(
        name="Acme Corporation",
        slug="acme",
    )

    repository.get_by_slug.return_value = tenant

    result = service.get_tenant_by_slug(
        db,
        "acme",
    )

    assert result is tenant

    repository.get_by_slug.assert_called_once_with(
        db,
        "acme",
    )


def test_list_active_tenants():
    db = MagicMock()
    repository = MagicMock()
    service = TenantService(repository)

    tenants = [
        Tenant(
            name="Acme Corporation",
            slug="acme",
        ),
        Tenant(
            name="Globex Corporation",
            slug="globex",
        ),
    ]

    repository.list_active.return_value = tenants

    result = service.list_active_tenants(db)

    assert result == tenants

    repository.list_active.assert_called_once_with(db)