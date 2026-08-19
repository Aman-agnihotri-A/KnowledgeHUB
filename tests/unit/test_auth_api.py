from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.auth import user_service
from app.main import app
from app.models.enums import UserRole


client = TestClient(app)


def test_login_returns_access_token():
    user = MagicMock()

    user.id = uuid4()
    user.email = "user@example.com"
    user.role = UserRole.SUB_USER
    user.tenant_id = uuid4()

    original_authenticate = user_service.authenticate_user

    user_service.authenticate_user = MagicMock(
        return_value=user,
    )

    try:
        response = client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "password",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert "access_token" in data
        assert data["access_token"]
        assert data["token_type"] == "bearer"

    finally:
        user_service.authenticate_user = original_authenticate


def test_login_rejects_invalid_credentials():
    original_authenticate = user_service.authenticate_user

    user_service.authenticate_user = MagicMock(
        return_value=None,
    )

    try:
        response = client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "wrong-password",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == (
            "Invalid email or password."
        )

    finally:
        user_service.authenticate_user = original_authenticate