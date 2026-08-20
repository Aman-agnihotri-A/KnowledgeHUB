from unittest.mock import ANY,MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.tenants import tenant_service, user_service
from app.dependencies.auth import get_current_user
from app.main import app
from app.models.enums import UserRole
from app.models.tenant import Tenant
from app.models.user import User


client = TestClient(app)


def make_tenant(
    name: str = "Acme Corporation",
    slug: str = "acme",
) -> Tenant:
    return Tenant(
        id=uuid4(),
        name=name,
        slug=slug,
        is_active=True,
    )


def authenticate_as(
    *,
    role: UserRole,
    tenant_id=None,
):
    user = MagicMock(spec=User)

    user.id = uuid4()
    user.role = role
    user.tenant_id = tenant_id
    user.is_active = True

    app.dependency_overrides[get_current_user] = (
        lambda: user
    )

    return user


def clear_authentication_override():
    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


def test_create_tenant_requires_authentication():
    response = client.post(
        "/tenants",
        json={
            "name": "Acme Corporation",
            "slug": "acme",
        },
    )

    assert response.status_code == 401


def test_create_tenant_super_admin():
    authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    tenant = make_tenant(
        name="Acme Corporation",
        slug="acme",
    )

    original_create = tenant_service.create_tenant
    tenant_service.create_tenant = MagicMock(
        return_value=tenant,
    )

    try:
        response = client.post(
            "/tenants",
            json={
                "name": "Acme Corporation",
                "slug": "acme",
            },
        )

        assert response.status_code == 201
        assert response.json()["name"] == (
            "Acme Corporation"
        )
        assert response.json()["slug"] == "acme"

    finally:
        tenant_service.create_tenant = original_create
        clear_authentication_override()


def test_tenant_admin_cannot_create_tenant():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    try:
        response = client.post(
            "/tenants",
            json={
                "name": "Acme Corporation",
                "slug": "acme",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_sub_user_cannot_create_tenant():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    try:
        response = client.post(
            "/tenants",
            json={
                "name": "Acme Corporation",
                "slug": "acme",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_create_tenant_rejects_duplicate_slug():
    authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    original_create = tenant_service.create_tenant
    tenant_service.create_tenant = MagicMock(
        side_effect=ValueError(
            "Tenant with slug 'acme' already exists."
        ),
    )

    try:
        response = client.post(
            "/tenants",
            json={
                "name": "Another Corporation",
                "slug": "acme",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Tenant with slug 'acme' already exists."
        )

    finally:
        tenant_service.create_tenant = original_create
        clear_authentication_override()


def test_list_tenants_requires_authentication():
    response = client.get("/tenants")

    assert response.status_code == 401


def test_list_tenants_super_admin():
    authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    tenants = [
        make_tenant(
            name="Acme Corporation",
            slug="acme",
        ),
        make_tenant(
            name="Globex Corporation",
            slug="globex",
        ),
    ]

    original_list = tenant_service.list_active_tenants
    tenant_service.list_active_tenants = MagicMock(
        return_value=tenants,
    )

    try:
        response = client.get("/tenants")

        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["slug"] == "acme"

    finally:
        tenant_service.list_active_tenants = original_list
        clear_authentication_override()


def test_tenant_admin_cannot_list_all_tenants():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    try:
        response = client.get("/tenants")

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_get_tenant_requires_authentication():
    tenant_id = uuid4()

    response = client.get(
        f"/tenants/{tenant_id}",
    )

    assert response.status_code == 401


def test_super_admin_can_get_any_tenant():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    tenant = make_tenant(
        name="Acme Corporation",
        slug="acme",
    )

    original_get = tenant_service.get_tenant
    tenant_service.get_tenant = MagicMock(
        return_value=tenant,
    )

    try:
        response = client.get(
            f"/tenants/{tenant_id}",
        )

        assert response.status_code == 200
        assert response.json()["slug"] == "acme"

    finally:
        tenant_service.get_tenant = original_get
        clear_authentication_override()


def test_tenant_admin_can_get_own_tenant():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    tenant = make_tenant(
        name="Acme Corporation",
        slug="acme",
    )

    original_get = tenant_service.get_tenant
    tenant_service.get_tenant = MagicMock(
        return_value=tenant,
    )

    try:
        response = client.get(
            f"/tenants/{tenant_id}",
        )

        assert response.status_code == 200

    finally:
        tenant_service.get_tenant = original_get
        clear_authentication_override()


def test_tenant_admin_cannot_get_other_tenant():
    own_tenant_id = uuid4()
    other_tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=own_tenant_id,
    )

    try:
        response = client.get(
            f"/tenants/{other_tenant_id}",
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_sub_user_can_get_own_tenant():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    tenant = make_tenant(
        name="Acme Corporation",
        slug="acme",
    )

    original_get = tenant_service.get_tenant
    tenant_service.get_tenant = MagicMock(
        return_value=tenant,
    )

    try:
        response = client.get(
            f"/tenants/{tenant_id}",
        )

        assert response.status_code == 200

    finally:
        tenant_service.get_tenant = original_get
        clear_authentication_override()


def test_sub_user_cannot_get_other_tenant():
    own_tenant_id = uuid4()
    other_tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=own_tenant_id,
    )

    try:
        response = client.get(
            f"/tenants/{other_tenant_id}",
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_get_missing_tenant_returns_404():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    original_get = tenant_service.get_tenant
    tenant_service.get_tenant = MagicMock(
        return_value=None,
    )

    try:
        response = client.get(
            f"/tenants/{tenant_id}",
        )

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Tenant not found."
        )

    finally:
        tenant_service.get_tenant = original_get
        clear_authentication_override()


def test_create_sub_user_as_tenant_admin():
    tenant_id = uuid4()

    current_user = authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    user = User(
        email="user@example.com",
        hashed_password="hashed-password",
        full_name="Sub User",
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
        is_active=True,
    )

    user.id = uuid4()

    original_create = user_service.create_user
    user_service.create_user = MagicMock(
        return_value=user,
    )

    try:
        response = client.post(
            f"/tenants/{tenant_id}/users",
            json={
                "email": "user@example.com",
                "password": "password",
                "full_name": "Sub User",
                "role": "sub_user",
            },
        )

        assert response.status_code == 201
        assert response.json()["email"] == (
            "user@example.com"
        )
        assert "hashed_password" not in response.json()

        user_service.create_user.assert_called_once_with(
            __import__("unittest").mock.ANY,
            email="user@example.com",
            password="password",
            full_name="Sub User",
            role=UserRole.SUB_USER,
            tenant_id=tenant_id,
        )

    finally:
        user_service.create_user = original_create
        clear_authentication_override()


def test_tenant_admin_cannot_create_tenant_admin():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    try:
        response = client.post(
            f"/tenants/{tenant_id}/users",
            json={
                "email": "admin@example.com",
                "password": "password",
                "full_name": "Another Admin",
                "role": "tenant_admin",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_tenant_admin_cannot_create_super_admin():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    try:
        response = client.post(
            f"/tenants/{tenant_id}/users",
            json={
                "email": "admin@example.com",
                "password": "password",
                "full_name": "Super Admin",
                "role": "super_admin",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_super_admin_can_create_tenant_admin():
    tenant_id = uuid4()

    current_user = authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    user = User(
        email="admin@example.com",
        hashed_password="hashed-password",
        full_name="Tenant Admin",
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
        is_active=True,
    )

    user.id = uuid4()

    original_create = user_service.create_user
    user_service.create_user = MagicMock(
        return_value=user,
    )

    try:
        response = client.post(
            f"/tenants/{tenant_id}/users",
            json={
                "email": "admin@example.com",
                "password": "password",
                "full_name": "Tenant Admin",
                "role": "tenant_admin",
            },
        )

        assert response.status_code == 201
        assert response.json()["role"] == "tenant_admin"

    finally:
        user_service.create_user = original_create
        clear_authentication_override()


def test_super_admin_cannot_create_super_admin():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    try:
        response = client.post(
            f"/tenants/{tenant_id}/users",
            json={
                "email": "admin@example.com",
                "password": "password",
                "full_name": "Super Admin",
                "role": "super_admin",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_sub_user_cannot_create_users():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    try:
        response = client.post(
            f"/tenants/{tenant_id}/users",
            json={
                "email": "user@example.com",
                "password": "password",
                "full_name": "Sub User",
                "role": "sub_user",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_tenant_admin_cannot_create_user_in_other_tenant():
    own_tenant_id = uuid4()
    other_tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=own_tenant_id,
    )

    try:
        response = client.post(
            f"/tenants/{other_tenant_id}/users",
            json={
                "email": "user@example.com",
                "password": "password",
                "full_name": "Sub User",
                "role": "sub_user",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_create_user_duplicate_email_returns_400():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    original_create = user_service.create_user
    user_service.create_user = MagicMock(
        side_effect=ValueError(
            "User with email 'user@example.com' already exists."
        ),
    )

    try:
        response = client.post(
            f"/tenants/{tenant_id}/users",
            json={
                "email": "user@example.com",
                "password": "password",
                "full_name": "Sub User",
                "role": "sub_user",
            },
        )

        assert response.status_code == 400

    finally:
        user_service.create_user = original_create
        clear_authentication_override()


def test_list_users_requires_authentication():
    tenant_id = uuid4()

    response = client.get(
        f"/tenants/{tenant_id}/users",
    )

    assert response.status_code == 401


def test_tenant_admin_can_list_own_users():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    users = [
        User(
            email="one@example.com",
            hashed_password="hashed-password",
            full_name="One",
            role=UserRole.SUB_USER,
            tenant_id=tenant_id,
            is_active=True,
        ),
        User(
            email="two@example.com",
            hashed_password="hashed-password",
            full_name="Two",
            role=UserRole.SUB_USER,
            tenant_id=tenant_id,
            is_active=True,
        ),
    ]

    for user in users:
        user.id = uuid4()

    original_list = user_service.list_active_tenant_users
    user_service.list_active_tenant_users = MagicMock(
        return_value=users,
    )

    try:
        response = client.get(
            f"/tenants/{tenant_id}/users",
        )

        assert response.status_code == 200
        assert len(response.json()) == 2
        assert "hashed_password" not in response.text

    finally:
        user_service.list_active_tenant_users = original_list
        clear_authentication_override()


def test_tenant_admin_cannot_list_other_tenant_users():
    own_tenant_id = uuid4()
    other_tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=own_tenant_id,
    )

    try:
        response = client.get(
            f"/tenants/{other_tenant_id}/users",
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_sub_user_cannot_list_users():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    try:
        response = client.get(
            f"/tenants/{tenant_id}/users",
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_super_admin_can_list_any_tenant_users():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    original_list = user_service.list_active_tenant_users
    user_service.list_active_tenant_users = MagicMock(
        return_value=[],
    )

    try:
        response = client.get(
            f"/tenants/{tenant_id}/users",
        )

        assert response.status_code == 200
        assert response.json() == []

    finally:
        user_service.list_active_tenant_users = original_list
        clear_authentication_override()

def test_update_user_status_requires_authentication():
    tenant_id = uuid4()
    user_id = uuid4()

    response = client.patch(
        f"/tenants/{tenant_id}/users/{user_id}/status",
        json={"is_active": False},
    )

    assert response.status_code == 401


def test_tenant_admin_can_deactivate_sub_user():
    tenant_id = uuid4()
    user_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    user = User(
        id=user_id,
        email="user@example.com",
        hashed_password="hashed-password",
        full_name="Sub User",
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
        is_active=False,
    )

    original_get = user_service.get_user
    original_update = user_service.update_user_status

    user_service.get_user = MagicMock(
        return_value=user,
    )
    user_service.update_user_status = MagicMock(
        return_value=user,
    )

    try:
        response = client.patch(
            f"/tenants/{tenant_id}/users/{user_id}/status",
            json={"is_active": False},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

        user_service.update_user_status.assert_called_once_with(
            ANY,
            user_id=user_id,
            tenant_id=tenant_id,
            is_active=False,
        )

    finally:
        user_service.get_user = original_get
        user_service.update_user_status = original_update
        clear_authentication_override()


def test_tenant_admin_can_reactivate_sub_user():
    tenant_id = uuid4()
    user_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    user = User(
        id=user_id,
        email="user@example.com",
        hashed_password="hashed-password",
        full_name="Sub User",
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
        is_active=True,
    )

    original_get = user_service.get_user
    original_update = user_service.update_user_status

    user_service.get_user = MagicMock(
        return_value=user,
    )
    user_service.update_user_status = MagicMock(
        return_value=user,
    )

    try:
        response = client.patch(
            f"/tenants/{tenant_id}/users/{user_id}/status",
            json={"is_active": True},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is True

    finally:
        user_service.get_user = original_get
        user_service.update_user_status = original_update
        clear_authentication_override()


def test_tenant_admin_cannot_modify_tenant_admin():
    tenant_id = uuid4()
    user_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    user = User(
        id=user_id,
        email="admin@example.com",
        hashed_password="hashed-password",
        full_name="Another Admin",
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
        is_active=True,
    )

    original_get = user_service.get_user
    user_service.get_user = MagicMock(
        return_value=user,
    )

    try:
        response = client.patch(
            f"/tenants/{tenant_id}/users/{user_id}/status",
            json={"is_active": False},
        )

        assert response.status_code == 403

    finally:
        user_service.get_user = original_get
        clear_authentication_override()


def test_tenant_admin_cannot_modify_user_in_other_tenant():
    own_tenant_id = uuid4()
    other_tenant_id = uuid4()
    user_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=own_tenant_id,
    )

    try:
        response = client.patch(
            f"/tenants/{other_tenant_id}/users/{user_id}/status",
            json={"is_active": False},
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_sub_user_cannot_modify_user_status():
    tenant_id = uuid4()
    user_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    try:
        response = client.patch(
            f"/tenants/{tenant_id}/users/{user_id}/status",
            json={"is_active": False},
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_super_admin_can_deactivate_tenant_admin():
    tenant_id = uuid4()
    user_id = uuid4()

    authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    user = User(
        id=user_id,
        email="admin@example.com",
        hashed_password="hashed-password",
        full_name="Tenant Admin",
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
        is_active=False,
    )

    original_get = user_service.get_user
    original_update = user_service.update_user_status

    user_service.get_user = MagicMock(
        return_value=user,
    )
    user_service.update_user_status = MagicMock(
        return_value=user,
    )

    try:
        response = client.patch(
            f"/tenants/{tenant_id}/users/{user_id}/status",
            json={"is_active": False},
        )

        assert response.status_code == 200
        assert response.json()["role"] == "tenant_admin"
        assert response.json()["is_active"] is False

    finally:
        user_service.get_user = original_get
        user_service.update_user_status = original_update
        clear_authentication_override()


def test_update_user_status_missing_user_returns_404():
    tenant_id = uuid4()
    user_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    original_get = user_service.get_user
    user_service.get_user = MagicMock(
        return_value=None,
    )

    try:
        response = client.patch(
            f"/tenants/{tenant_id}/users/{user_id}/status",
            json={"is_active": False},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found."

    finally:
        user_service.get_user = original_get
        clear_authentication_override()


def test_update_user_status_invalid_payload_returns_422():
    tenant_id = uuid4()
    user_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    try:
        response = client.patch(
            f"/tenants/{tenant_id}/users/{user_id}/status",
            json={"is_active": "not-a-boolean"},
        )

        assert response.status_code == 422

    finally:
        clear_authentication_override()