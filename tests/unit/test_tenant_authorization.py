from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.dependencies.authorization import require_tenant_access
from app.models.enums import UserRole
from app.models.user import User


def make_user(
    role: UserRole,
    tenant_id=None,
) -> User:
    user = User(
        email=f"{uuid4()}@example.com",
        hashed_password="hashed-password",
        full_name="Test User",
        role=role,
        tenant_id=tenant_id,
        is_active=True,
    )

    user.id = uuid4()

    return user


def test_super_admin_can_access_any_tenant():
    target_tenant = uuid4()

    user = make_user(
        UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    result = require_tenant_access(
        tenant_id=target_tenant,
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
    user_tenant = uuid4()
    target_tenant = uuid4()

    user = make_user(
        UserRole.TENANT_ADMIN,
        tenant_id=user_tenant,
    )

    with pytest.raises(HTTPException) as exc_info:
        require_tenant_access(
            tenant_id=target_tenant,
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
    user_tenant = uuid4()
    target_tenant = uuid4()

    user = make_user(
        UserRole.SUB_USER,
        tenant_id=user_tenant,
    )

    with pytest.raises(HTTPException) as exc_info:
        require_tenant_access(
            tenant_id=target_tenant,
            current_user=user,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "User does not have access to this tenant."
    )