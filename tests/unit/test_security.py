from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.security import create_access_token

from app.core.security import hash_password, verify_password


def test_hash_password_does_not_return_plaintext():
    password = "super-secret-password"

    hashed_password = hash_password(password)

    assert hashed_password != password


def test_verify_password_accepts_correct_password():
    password = "super-secret-password"

    hashed_password = hash_password(password)

    assert verify_password(
        password,
        hashed_password,
    )


def test_verify_password_rejects_wrong_password():
    password = "super-secret-password"

    hashed_password = hash_password(password)

    assert not verify_password(
        "wrong-password",
        hashed_password,
    )


def test_same_password_generates_different_hashes():
    password = "super-secret-password"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash

def test_create_access_token_contains_expected_claims():
    token = create_access_token(
        user_id="123",
        role="sub_user",
        tenant_id="456",
    )

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == "123"
    assert payload["role"] == "sub_user"
    assert payload["tenant_id"] == "456"
    assert "iat" in payload
    assert "exp" in payload


def test_create_access_token_supports_super_admin_without_tenant():
    token = create_access_token(
        user_id="123",
        role="super_admin",
        tenant_id=None,
    )

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == "123"
    assert payload["role"] == "super_admin"
    assert payload["tenant_id"] is None


def test_access_token_has_expiration():
    token = create_access_token(
        user_id="123",
        role="sub_user",
        tenant_id="456",
    )

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["exp"] > payload["iat"]

def test_decode_access_token_returns_payload():
    token = create_access_token(
        user_id="123",
        role="sub_user",
        tenant_id="456",
    )

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == "123"
    assert payload["role"] == "sub_user"
    assert payload["tenant_id"] == "456"


def test_decode_access_token_rejects_invalid_token():
    with pytest.raises(ValueError):
        from app.core.security import decode_access_token

        decode_access_token("invalid-token")


def test_decode_access_token_rejects_expired_token():
    expired_token = jwt.encode(
        {
            "sub": "123",
            "role": "sub_user",
            "tenant_id": "456",
            "exp": datetime.now(timezone.utc)
            - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    from app.core.security import decode_access_token

    with pytest.raises(ValueError):
        decode_access_token(expired_token)