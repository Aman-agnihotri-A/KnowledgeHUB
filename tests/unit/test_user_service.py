from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.enums import UserRole
from app.models.user import User
from app.services.user import UserService


def test_create_super_admin_without_tenant():
    db = MagicMock()
    repository = MagicMock()
    service = UserService(repository)

    user = User(
        email="admin@example.com",
        hashed_password="hashed-password",
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
    )

    repository.get_by_email.return_value = None
    repository.create.return_value = user

    result = service.create_user(
        db,
        email="admin@example.com",
        hashed_password="hashed-password",
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
    )

    assert result is user

    repository.get_by_email.assert_called_once_with(
        db,
        "admin@example.com",
    )

    repository.create.assert_called_once_with(
        db,
        email="admin@example.com",
        hashed_password="hashed-password",
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )


def test_create_tenant_admin_requires_tenant():
    db = MagicMock()
    repository = MagicMock()
    service = UserService(repository)

    repository.get_by_email.return_value = None

    with pytest.raises(
        ValueError,
        match="tenant_admin must belong to a tenant.",
    ):
        service.create_user(
            db,
            email="admin@example.com",
            hashed_password="hashed-password",
            full_name="Tenant Admin",
            role=UserRole.TENANT_ADMIN,
        )

    repository.create.assert_not_called()


def test_create_sub_user_requires_tenant():
    db = MagicMock()
    repository = MagicMock()
    service = UserService(repository)

    repository.get_by_email.return_value = None

    with pytest.raises(
        ValueError,
        match="sub_user must belong to a tenant.",
    ):
        service.create_user(
            db,
            email="user@example.com",
            hashed_password="hashed-password",
            full_name="Sub User",
            role=UserRole.SUB_USER,
        )

    repository.create.assert_not_called()


def test_super_admin_cannot_belong_to_tenant():
    db = MagicMock()
    repository = MagicMock()
    service = UserService(repository)

    repository.get_by_email.return_value = None

    tenant_id = uuid4()

    with pytest.raises(
        ValueError,
        match="Super Admin cannot belong to a tenant.",
    ):
        service.create_user(
            db,
            email="admin@example.com",
            hashed_password="hashed-password",
            full_name="Super Admin",
            role=UserRole.SUPER_ADMIN,
            tenant_id=tenant_id,
        )

    repository.create.assert_not_called()


def test_create_tenant_admin():
    db = MagicMock()
    repository = MagicMock()
    service = UserService(repository)

    tenant_id = uuid4()

    user = User(
        email="admin@example.com",
        hashed_password="hashed-password",
        full_name="Tenant Admin",
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    repository.get_by_email.return_value = None
    repository.create.return_value = user

    result = service.create_user(
        db,
        email="admin@example.com",
        hashed_password="hashed-password",
        full_name="Tenant Admin",
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    assert result is user

    repository.create.assert_called_once_with(
        db,
        email="admin@example.com",
        hashed_password="hashed-password",
        full_name="Tenant Admin",
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )


def test_create_user_rejects_duplicate_email():
    db = MagicMock()
    repository = MagicMock()
    service = UserService(repository)

    existing_user = User(
        email="existing@example.com",
        hashed_password="hashed-password",
        full_name="Existing User",
        role=UserRole.SUB_USER,
        tenant_id=uuid4(),
    )

    repository.get_by_email.return_value = existing_user

    with pytest.raises(
        ValueError,
        match="User with email 'existing@example.com' already exists.",
    ):
        service.create_user(
            db,
            email="existing@example.com",
            hashed_password="hashed-password",
            full_name="Another User",
            role=UserRole.SUB_USER,
            tenant_id=uuid4(),
        )

    repository.create.assert_not_called()


def test_get_user():
    db = MagicMock()
    repository = MagicMock()
    service = UserService(repository)

    user_id = uuid4()

    user = User(
        email="user@example.com",
        hashed_password="hashed-password",
        full_name="Test User",
        role=UserRole.SUB_USER,
        tenant_id=uuid4(),
    )

    repository.get_by_id.return_value = user

    result = service.get_user(
        db,
        user_id,
    )

    assert result is user

    repository.get_by_id.assert_called_once_with(
        db,
        user_id,
    )


def test_get_user_by_email():
    db = MagicMock()
    repository = MagicMock()
    service = UserService(repository)

    user = User(
        email="user@example.com",
        hashed_password="hashed-password",
        full_name="Test User",
        role=UserRole.SUB_USER,
        tenant_id=uuid4(),
    )

    repository.get_by_email.return_value = user

    result = service.get_user_by_email(
        db,
        "user@example.com",
    )

    assert result is user

    repository.get_by_email.assert_called_once_with(
        db,
        "user@example.com",
    )


def test_list_tenant_users():
    db = MagicMock()
    repository = MagicMock()
    service = UserService(repository)

    tenant_id = uuid4()

    users = [
        User(
            email="one@example.com",
            hashed_password="hashed-password",
            full_name="User One",
            role=UserRole.SUB_USER,
            tenant_id=tenant_id,
        ),
        User(
            email="two@example.com",
            hashed_password="hashed-password",
            full_name="User Two",
            role=UserRole.SUB_USER,
            tenant_id=tenant_id,
        ),
    ]

    repository.list_by_tenant.return_value = users

    result = service.list_tenant_users(
        db,
        tenant_id,
    )

    assert result == users

    repository.list_by_tenant.assert_called_once_with(
        db,
        tenant_id,
    )


def test_list_active_tenant_users():
    db = MagicMock()
    repository = MagicMock()
    service = UserService(repository)

    tenant_id = uuid4()

    users = [
        User(
            email="active@example.com",
            hashed_password="hashed-password",
            full_name="Active User",
            role=UserRole.SUB_USER,
            tenant_id=tenant_id,
            is_active=True,
        )
    ]

    repository.list_active_by_tenant.return_value = users

    result = service.list_active_tenant_users(
        db,
        tenant_id,
    )

    assert result == users

    repository.list_active_by_tenant.assert_called_once_with(
        db,
        tenant_id,
    )