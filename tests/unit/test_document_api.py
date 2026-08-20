from uuid import uuid4
from unittest.mock import ANY, MagicMock

import pytest

from app.dependencies.auth import get_current_user
from app.models.user import User

from fastapi.testclient import TestClient

from app.api.documents import document_service
from app.core.security import create_access_token
from app.main import app
from app.models.enums import UserRole


client = TestClient(app)

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

def make_auth_headers(
    *,
    user_id=None,
    role=UserRole.TENANT_ADMIN,
    tenant_id=None,
):
    user_id = user_id or uuid4()

    token = create_access_token(
        user_id=str(user_id),
        role=role.value,
        tenant_id=(
            str(tenant_id)
            if tenant_id is not None
            else None
        ),
    )

    return {
        "Authorization": f"Bearer {token}",
    }, user_id


def test_create_document_requires_authentication():
    tenant_id = uuid4()

    response = client.post(
        f"/documents/{tenant_id}",
        json={
            "filename": "knowledge.pdf",
            "storage_path": "documents/knowledge.pdf",
        },
    )

    assert response.status_code == 401


def test_create_document_rejects_invalid_jwt():
    tenant_id = uuid4()

    response = client.post(
        f"/documents/{tenant_id}",
        headers={
            "Authorization": "Bearer invalid-token",
        },
        json={
            "filename": "knowledge.pdf",
            "storage_path": "documents/knowledge.pdf",
        },
    )

    assert response.status_code == 401


def test_create_document_uses_authenticated_user_identity():
    tenant_id = uuid4()

    user = authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    document_id = uuid4()

    document = MagicMock()
    document.id = document_id
    document.tenant_id = tenant_id
    document.uploaded_by = user.id
    document.filename = "knowledge.pdf"
    document.storage_path = "documents/knowledge.pdf"
    document.status = "UPLOADED"

    original_service = document_service.create_document
    document_service.create_document = MagicMock(
        return_value=document,
    )

    try:
        response = client.post(
            f"/documents/{tenant_id}",
            params={
                "uploaded_by": str(uuid4()),
            },
            json={
                "filename": "knowledge.pdf",
                "storage_path": "documents/knowledge.pdf",
            },
        )

        assert response.status_code == 201

        document_service.create_document.assert_called_once_with(
            ANY,
            tenant_id=tenant_id,
            uploaded_by=user.id,
            filename="knowledge.pdf",
            storage_path="documents/knowledge.pdf",
        )

        assert response.json()["uploaded_by"] == str(user.id)

    finally:
        document_service.create_document = original_service
        clear_authentication_override()

def test_create_document_tenant_admin_own_tenant():
    tenant_id = uuid4()

    user = authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    document = MagicMock()
    document.id = uuid4()
    document.tenant_id = tenant_id
    document.uploaded_by = user.id
    document.filename = "knowledge.pdf"
    document.storage_path = "documents/knowledge.pdf"
    document.status = "UPLOADED"

    original_service = document_service.create_document
    document_service.create_document = MagicMock(
        return_value=document,
    )

    try:
        response = client.post(
            f"/documents/{tenant_id}",
            json={
                "filename": "knowledge.pdf",
                "storage_path": "documents/knowledge.pdf",
            },
        )

        assert response.status_code == 201

    finally:
        document_service.create_document = original_service
        clear_authentication_override()

def test_create_document_tenant_admin_other_tenant():
    user_tenant_id = uuid4()
    requested_tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=user_tenant_id,
    )

    try:
        response = client.post(
            f"/documents/{requested_tenant_id}",
            json={
                "filename": "knowledge.pdf",
                "storage_path": "documents/knowledge.pdf",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()

def test_create_document_sub_user_own_tenant_reaches_service():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    original_service = document_service.create_document
    document_service.create_document = MagicMock(
        side_effect=ValueError(
            "User does not have permission to upload documents."
        ),
    )

    try:
        response = client.post(
            f"/documents/{tenant_id}",
            json={
                "filename": "knowledge.pdf",
                "storage_path": "documents/knowledge.pdf",
            },
        )

        assert response.status_code == 400

    finally:
        document_service.create_document = original_service
        clear_authentication_override()

def test_create_document_super_admin_can_access_other_tenant():
    tenant_id = uuid4()

    user = authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    document = MagicMock()
    document.id = uuid4()
    document.tenant_id = tenant_id
    document.uploaded_by = user.id
    document.filename = "knowledge.pdf"
    document.storage_path = "documents/knowledge.pdf"
    document.status = "UPLOADED"

    original_service = document_service.create_document
    document_service.create_document = MagicMock(
        return_value=document,
    )

    try:
        response = client.post(
            f"/documents/{tenant_id}",
            json={
                "filename": "knowledge.pdf",
                "storage_path": "documents/knowledge.pdf",
            },
        )

        assert response.status_code == 201

    finally:
        document_service.create_document = original_service
        clear_authentication_override()

def test_list_documents_requires_authentication():
    tenant_id = uuid4()

    response = client.get(
        f"/documents/{tenant_id}",
    )

    assert response.status_code == 401


def test_list_documents_rejects_invalid_jwt():
    tenant_id = uuid4()

    response = client.get(
        f"/documents/{tenant_id}",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


def test_list_documents_tenant_admin_own_tenant():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    original_service = document_service.list_tenant_documents
    document_service.list_tenant_documents = MagicMock(
        return_value=[],
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}",
        )

        assert response.status_code == 200
        assert response.json() == []

    finally:
        document_service.list_tenant_documents = original_service
        clear_authentication_override()

def test_list_documents_tenant_admin_other_tenant():
    user_tenant_id = uuid4()
    requested_tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=user_tenant_id,
    )

    try:
        response = client.get(
            f"/documents/{requested_tenant_id}",
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_list_documents_sub_user_own_tenant():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    original_service = document_service.list_tenant_documents
    document_service.list_tenant_documents = MagicMock(
        return_value=[],
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}",
        )

        assert response.status_code == 200

    finally:
        document_service.list_tenant_documents = original_service
        clear_authentication_override()


def test_list_documents_sub_user_other_tenant():
    user_tenant_id = uuid4()
    requested_tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=user_tenant_id,
    )

    try:
        response = client.get(
            f"/documents/{requested_tenant_id}",
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_list_documents_super_admin_other_tenant():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    original_service = document_service.list_tenant_documents
    document_service.list_tenant_documents = MagicMock(
        return_value=[],
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}",
        )

        assert response.status_code == 200

    finally:
        document_service.list_tenant_documents = original_service
        clear_authentication_override()


def test_get_document_requires_authentication():
    tenant_id = uuid4()
    document_id = uuid4()

    response = client.get(
        f"/documents/{tenant_id}/{document_id}",
    )

    assert response.status_code == 401


def test_get_document_rejects_invalid_jwt():
    tenant_id = uuid4()
    document_id = uuid4()

    response = client.get(
        f"/documents/{tenant_id}/{document_id}",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


def test_get_document_tenant_admin_own_tenant():
    tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    original_service = document_service.get_document
    document_service.get_document = MagicMock(
        return_value=MagicMock(
            id=document_id,
            tenant_id=tenant_id,
            uploaded_by=uuid4(),
            filename="knowledge.pdf",
            storage_path="documents/knowledge.pdf",
            status="UPLOADED",
        ),
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}/{document_id}",
        )

        assert response.status_code == 200
        assert response.json()["id"] == str(document_id)

    finally:
        document_service.get_document = original_service
        clear_authentication_override()


def test_get_document_tenant_admin_other_tenant():
    user_tenant_id = uuid4()
    requested_tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=user_tenant_id,
    )

    try:
        response = client.get(
            f"/documents/{requested_tenant_id}/{document_id}",
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_get_document_sub_user_own_tenant():
    tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    original_service = document_service.get_document
    document_service.get_document = MagicMock(
        return_value=MagicMock(
            id=document_id,
            tenant_id=tenant_id,
            uploaded_by=uuid4(),
            filename="knowledge.pdf",
            storage_path="documents/knowledge.pdf",
            status="UPLOADED",
        ),
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}/{document_id}",
        )

        assert response.status_code == 200

    finally:
        document_service.get_document = original_service
        clear_authentication_override()


def test_get_document_sub_user_other_tenant():
    user_tenant_id = uuid4()
    requested_tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=user_tenant_id,
    )

    try:
        response = client.get(
            f"/documents/{requested_tenant_id}/{document_id}",
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_get_document_super_admin_other_tenant():
    tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    original_service = document_service.get_document
    document_service.get_document = MagicMock(
        return_value=MagicMock(
            id=document_id,
            tenant_id=tenant_id,
            uploaded_by=uuid4(),
            filename="knowledge.pdf",
            storage_path="documents/knowledge.pdf",
            status="UPLOADED",
        ),
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}/{document_id}",
        )

        assert response.status_code == 200

    finally:
        document_service.get_document = original_service
        clear_authentication_override()


def test_get_document_not_found_for_authorized_user():
    tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    original_service = document_service.get_document
    document_service.get_document = MagicMock(
        return_value=None,
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}/{document_id}",
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Document not found."

    finally:
        document_service.get_document = original_service
        clear_authentication_override()