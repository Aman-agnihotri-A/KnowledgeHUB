from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        password,
        hashed_password,
    )


def create_access_token(
    *,
    user_id: str,
    role: str,
    tenant_id: str | None,
) -> str:
    now = datetime.now(timezone.utc)

    expire = now + timedelta(
        minutes=settings.access_token_expire_minutes,
    )

    payload = {
        "sub": user_id,
        "role": role,
        "tenant_id": tenant_id,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )