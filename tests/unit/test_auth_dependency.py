from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.security import create_access_token
from app.dependencies.auth import get_current_user
from app.models.enums import UserRole
from app.models.user import User


def test_get_current_user_returns_user():
    db = MagicMock()

    user = User(
        email="user@example.com",
        hashed_password="hashed-password",
        full_name="Test User",
        role=UserRole.SUB_USER,
        tenant_id=uuid4(),
        is_active=True,
    )

    user.id = uuid4()

    token = create_access_token(
        user_id=str(user.id),
        role=user.role.value,
        tenant_id=str(user.tenant_id),
    )

    from app.dependencies.auth import user_service

    original_get_user = user_service.get_user
    user_service.get_user = MagicMock(
        return_value=user,
    )

    credentials = MagicMock()
    credentials.credentials = token

    try:
        result = get_current_user(
            credentials=credentials,
            db=db,
        )

        assert result is user

        user_service.get_user.assert_called_once_with(
            db,
            str(user.id),
        )

    finally:
        user_service.get_user = original_get_user


def test_get_current_user_rejects_invalid_token():
    db = MagicMock()

    credentials = MagicMock()
    credentials.credentials = "invalid-token"

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == (
        "Invalid or expired access token."
    )


def test_get_current_user_rejects_token_without_subject():
    db = MagicMock()

    token = jwt.encode(
        {
            "role": "sub_user",
            "tenant_id": str(uuid4()),
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    credentials = MagicMock()
    credentials.credentials = token

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == (
        "Invalid access token."
    )


def test_get_current_user_rejects_unknown_user():
    db = MagicMock()

    user_id = uuid4()

    token = create_access_token(
        user_id=str(user_id),
        role="sub_user",
        tenant_id=str(uuid4()),
    )

    from app.dependencies.auth import user_service

    original_get_user = user_service.get_user
    user_service.get_user = MagicMock(
        return_value=None,
    )

    credentials = MagicMock()
    credentials.credentials = token

    try:
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(
                credentials=credentials,
                db=db,
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "User not found."

    finally:
        user_service.get_user = original_get_user


def test_get_current_user_rejects_inactive_user():
    db = MagicMock()

    user = User(
        email="inactive@example.com",
        hashed_password="hashed-password",
        full_name="Inactive User",
        role=UserRole.SUB_USER,
        tenant_id=uuid4(),
        is_active=False,
    )

    user.id = uuid4()

    token = create_access_token(
        user_id=str(user.id),
        role=user.role.value,
        tenant_id=str(user.tenant_id),
    )

    from app.dependencies.auth import user_service

    original_get_user = user_service.get_user
    user_service.get_user = MagicMock(
        return_value=user,
    )

    credentials = MagicMock()
    credentials.credentials = token

    try:
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(
                credentials=credentials,
                db=db,
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Inactive user."

    finally:
        user_service.get_user = original_get_user