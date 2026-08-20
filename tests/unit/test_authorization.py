from unittest.mock import MagicMock

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.dependencies.authorization import (
    require_role,
    require_tenant_access,
)
from app.models.enums import UserRole
from app.models.user import User


def make_user(role: UserRole) -> User:
    user = MagicMock(spec=User)
    user.role = role
    user.is_active = True
    return user


def test_require_role_allows_matching_role():
    user = make_user(UserRole.SUPER_ADMIN)

    dependency = require_role(UserRole.SUPER_ADMIN)

    result = dependency(current_user=user)

    assert result is user


def test_require_role_rejects_wrong_role():
    user = make_user(UserRole.SUB_USER)

    dependency = require_role(UserRole.SUPER_ADMIN)

    with pytest.raises(HTTPException) as exc_info:
        dependency(current_user=user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions."


def test_require_role_allows_any_of_multiple_roles():
    user = make_user(UserRole.TENANT_ADMIN)

    dependency = require_role(
        UserRole.SUPER_ADMIN,
        UserRole.TENANT_ADMIN,
    )

    result = dependency(current_user=user)

    assert result is user


def test_require_role_rejects_when_multiple_roles_do_not_match():
    user = make_user(UserRole.SUB_USER)

    dependency = require_role(
        UserRole.SUPER_ADMIN,
        UserRole.TENANT_ADMIN,
    )

    with pytest.raises(HTTPException) as exc_info:
        dependency(current_user=user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions."


def test_super_admin_role_is_supported():
    user = make_user(UserRole.SUPER_ADMIN)

    dependency = require_role(UserRole.SUPER_ADMIN)

    assert dependency(current_user=user) is user


def test_tenant_admin_role_is_supported():
    user = make_user(UserRole.TENANT_ADMIN)

    dependency = require_role(UserRole.TENANT_ADMIN)

    assert dependency(current_user=user) is user


def test_sub_user_role_is_supported():
    user = make_user(UserRole.SUB_USER)

    dependency = require_role(UserRole.SUB_USER)

    assert dependency(current_user=user) is user

def test_role_dependency_requires_current_user():
    dependency = require_role(UserRole.SUPER_ADMIN)

    assert dependency.__name__ == "role_dependency"

def make_user(
    role: UserRole,
    tenant_id=None,
) -> User:
    user = User(
        email="user@example.com",
        hashed_password="hashed-password",
        full_name="Test User",
        role=role,
        tenant_id=tenant_id,
        is_active=True,
    )

    user.id = uuid4()

    return user


def test_require_role_allows_matching_role():
    user = make_user(UserRole.SUPER_ADMIN)

    dependency = require_role(UserRole.SUPER_ADMIN)

    result = dependency(current_user=user)

    assert result is user


def test_require_role_rejects_wrong_role():
    user = make_user(UserRole.SUB_USER)

    dependency = require_role(UserRole.SUPER_ADMIN)

    with pytest.raises(HTTPException) as exc_info:
        dependency(current_user=user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions."


def test_require_role_allows_any_of_multiple_roles():
    user = make_user(UserRole.TENANT_ADMIN)

    dependency = require_role(
        UserRole.SUPER_ADMIN,
        UserRole.TENANT_ADMIN,
    )

    result = dependency(current_user=user)

    assert result is user


def test_require_role_rejects_when_multiple_roles_do_not_match():
    user = make_user(UserRole.SUB_USER)

    dependency = require_role(
        UserRole.SUPER_ADMIN,
        UserRole.TENANT_ADMIN,
    )

    with pytest.raises(HTTPException) as exc_info:
        dependency(current_user=user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions."


def test_super_admin_role_is_supported():
    user = make_user(UserRole.SUPER_ADMIN)

    dependency = require_role(UserRole.SUPER_ADMIN)

    assert dependency(current_user=user) is user


def test_tenant_admin_role_is_supported():
    user = make_user(
        UserRole.TENANT_ADMIN,
        tenant_id=uuid4(),
    )

    dependency = require_role(UserRole.TENANT_ADMIN)

    assert dependency(current_user=user) is user


def test_sub_user_role_is_supported():
    user = make_user(
        UserRole.SUB_USER,
        tenant_id=uuid4(),
    )

    dependency = require_role(UserRole.SUB_USER)

    assert dependency(current_user=user) is user


def test_role_dependency_requires_current_user():
    dependency = require_role(UserRole.SUPER_ADMIN)

    assert dependency.__name__ == "role_dependency"


def test_super_admin_can_access_any_tenant():
    tenant_id = uuid4()

    user = make_user(
        UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    result = require_tenant_access(
        tenant_id=tenant_id,
        current_user=user,
    )

    assert result is user


def test_tenant_admin_can_access_own_tenant():
    tenant_id = uuid4()

    user = make_user(
        UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    result = require_tenant_access(
        tenant_id=tenant_id,
        current_user=user,
    )

    assert result is user


def test_tenant_admin_cannot_access_other_tenant():
    tenant_id = uuid4()
    other_tenant_id = uuid4()

    user = make_user(
        UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    with pytest.raises(HTTPException) as exc_info:
        require_tenant_access(
            tenant_id=other_tenant_id,
            current_user=user,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "User does not have access to this tenant."
    )


def test_sub_user_can_access_own_tenant():
    tenant_id = uuid4()

    user = make_user(
        UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    result = require_tenant_access(
        tenant_id=tenant_id,
        current_user=user,
    )

    assert result is user


def test_sub_user_cannot_access_other_tenant():
    tenant_id = uuid4()
    other_tenant_id = uuid4()

    user = make_user(
        UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    with pytest.raises(HTTPException) as exc_info:
        require_tenant_access(
            tenant_id=other_tenant_id,
            current_user=user,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "User does not have access to this tenant."
    )