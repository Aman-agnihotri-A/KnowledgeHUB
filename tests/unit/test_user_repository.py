from unittest.mock import MagicMock
from uuid import uuid4

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user import UserRepository


def test_create_user():
    db = MagicMock()
    repository = UserRepository()

    tenant_id = uuid4()

    user = repository.create(
        db,
        email="admin@example.com",
        hashed_password="hashed-password",
        full_name="Tenant Admin",
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    assert user.email == "admin@example.com"
    assert user.hashed_password == "hashed-password"
    assert user.full_name == "Tenant Admin"
    assert user.role == UserRole.TENANT_ADMIN
    assert user.tenant_id == tenant_id

    db.add.assert_called_once_with(user)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(user)


def test_create_super_admin_without_tenant():
    db = MagicMock()
    repository = UserRepository()

    user = repository.create(
        db,
        email="superadmin@example.com",
        hashed_password="hashed-password",
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
    )

    assert user.email == "superadmin@example.com"
    assert user.role == UserRole.SUPER_ADMIN
    assert user.tenant_id is None


def test_get_user_by_id():
    db = MagicMock()
    repository = UserRepository()

    user_id = uuid4()

    user = User(
        email="user@example.com",
        hashed_password="hashed-password",
        full_name="Test User",
        role=UserRole.SUB_USER,
    )

    db.scalar.return_value = user

    result = repository.get_by_id(
        db,
        user_id,
    )

    assert result is user
    db.scalar.assert_called_once()


def test_get_user_by_email():
    db = MagicMock()
    repository = UserRepository()

    user = User(
        email="user@example.com",
        hashed_password="hashed-password",
        full_name="Test User",
        role=UserRole.SUB_USER,
    )

    db.scalar.return_value = user

    result = repository.get_by_email(
        db,
        "user@example.com",
    )

    assert result is user
    db.scalar.assert_called_once()


def test_list_users_by_tenant():
    db = MagicMock()
    repository = UserRepository()

    tenant_id = uuid4()

    user = User(
        email="user@example.com",
        hashed_password="hashed-password",
        full_name="Test User",
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    db.scalars.return_value.all.return_value = [user]

    result = repository.list_by_tenant(
        db,
        tenant_id,
    )

    assert result == [user]


def test_list_active_users_by_tenant():
    db = MagicMock()
    repository = UserRepository()

    tenant_id = uuid4()

    user = User(
        email="user@example.com",
        hashed_password="hashed-password",
        full_name="Test User",
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
        is_active=True,
    )

    db.scalars.return_value.all.return_value = [user]

    result = repository.list_active_by_tenant(
        db,
        tenant_id,
    )

    assert result == [user]