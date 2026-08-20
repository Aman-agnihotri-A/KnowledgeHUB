from uuid import uuid4
from unittest.mock import ANY, MagicMock

from pathlib import Path

import pytest

from app.dependencies.auth import get_current_user
from app.models.user import User

from fastapi.testclient import TestClient

from app.api.documents import document_service
from app.core.security import create_access_token
from app.main import app
from app.models.enums import UserRole, DocumentStatus


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
    document.status = DocumentStatus.UPLOADED

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
    document.status = DocumentStatus.UPLOADED

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
    document.status = DocumentStatus.UPLOADED

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
            status=DocumentStatus.UPLOADED,
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
            status=DocumentStatus.UPLOADED,
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
            status=DocumentStatus.UPLOADED,
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

def test_update_document_status_requires_authentication():
    tenant_id = uuid4()
    document_id = uuid4()

    response = client.patch(
        f"/documents/{tenant_id}/{document_id}/status",
        json={
            "status": "processing",
        },
    )

    assert response.status_code == 401


def test_update_document_status_rejects_invalid_jwt():
    tenant_id = uuid4()
    document_id = uuid4()

    response = client.patch(
        f"/documents/{tenant_id}/{document_id}/status",
        headers={
            "Authorization": "Bearer invalid-token",
        },
        json={
            "status": "processing",
        },
    )

    assert response.status_code == 401


def test_update_document_status_tenant_admin_own_tenant():
    tenant_id = uuid4()
    document_id = uuid4()

    user = authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    document = MagicMock()
    document.id = document_id
    document.tenant_id = tenant_id
    document.uploaded_by = user.id
    document.filename = "knowledge.pdf"
    document.storage_path = "documents/knowledge.pdf"
    document.status = DocumentStatus.PROCESSING

    original_service = document_service.update_document_status
    document_service.update_document_status = MagicMock(
        return_value=document,
    )

    try:
        response = client.patch(
            f"/documents/{tenant_id}/{document_id}/status",
            json={
                "status": "processing",
            },
        )

        assert response.status_code == 200

        document_service.update_document_status.assert_called_once_with(
            ANY,
            document_id=document_id,
            tenant_id=tenant_id,
            status=DocumentStatus.PROCESSING,
        )

    finally:
        document_service.update_document_status = original_service
        clear_authentication_override()


def test_update_document_status_super_admin_other_tenant():
    tenant_id = uuid4()
    document_id = uuid4()

    user = authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    document = MagicMock()
    document.id = document_id
    document.tenant_id = tenant_id
    document.uploaded_by = user.id
    document.filename = "knowledge.pdf"
    document.storage_path = "documents/knowledge.pdf"
    document.status = DocumentStatus.PROCESSING

    original_service = document_service.update_document_status
    document_service.update_document_status = MagicMock(
        return_value=document,
    )

    try:
        response = client.patch(
            f"/documents/{tenant_id}/{document_id}/status",
            json={
                "status": "processing",
            },
        )

        assert response.status_code == 200

    finally:
        document_service.update_document_status = original_service
        clear_authentication_override()


def test_update_document_status_tenant_admin_other_tenant():
    user_tenant_id = uuid4()
    requested_tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=user_tenant_id,
    )

    try:
        response = client.patch(
            f"/documents/{requested_tenant_id}/{document_id}/status",
            json={
                "status": "processing",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_update_document_status_sub_user_forbidden():
    tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    try:
        response = client.patch(
            f"/documents/{tenant_id}/{document_id}/status",
            json={
                "status": "processing",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_update_document_status_invalid_transition_returns_400():
    tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    original_service = document_service.update_document_status
    document_service.update_document_status = MagicMock(
        side_effect=ValueError(
            "Invalid document status transition: "
            "uploaded -> ready."
        ),
    )

    try:
        response = client.patch(
            f"/documents/{tenant_id}/{document_id}/status",
            json={
                "status": "ready",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Invalid document status transition: "
            "uploaded -> ready."
        )

    finally:
        document_service.update_document_status = original_service
        clear_authentication_override()


def test_update_document_status_missing_document_returns_404():
    tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    original_service = document_service.update_document_status
    document_service.update_document_status = MagicMock(
        side_effect=ValueError(
            "Document not found."
        ),
    )

    try:
        response = client.patch(
            f"/documents/{tenant_id}/{document_id}/status",
            json={
                "status": "processing",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Document not found."

    finally:
        document_service.update_document_status = original_service
        clear_authentication_override()


def test_update_document_status_cross_tenant_document_returns_400():
    tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    original_service = document_service.update_document_status
    document_service.update_document_status = MagicMock(
        side_effect=ValueError(
            "Document does not belong to the specified tenant."
        ),
    )

    try:
        response = client.patch(
            f"/documents/{tenant_id}/{document_id}/status",
            json={
                "status": "processing",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Document does not belong to the specified tenant."
        )

    finally:
        document_service.update_document_status = original_service
        clear_authentication_override()


def test_update_document_status_invalid_status_returns_422():
    tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    try:
        response = client.patch(
            f"/documents/{tenant_id}/{document_id}/status",
            json={
                "status": "invalid_status",
            },
        )

        assert response.status_code == 422

    finally:
        clear_authentication_override()

def test_list_documents_without_status():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    documents = [
        MagicMock(
            id=uuid4(),
            tenant_id=tenant_id,
            uploaded_by=uuid4(),
            filename="one.pdf",
            storage_path="documents/one.pdf",
            status=DocumentStatus.UPLOADED,
        ),
        MagicMock(
            id=uuid4(),
            tenant_id=tenant_id,
            uploaded_by=uuid4(),
            filename="two.pdf",
            storage_path="documents/two.pdf",
            status=DocumentStatus.READY,
        ),
    ]

    original_list = document_service.list_tenant_documents

    document_service.list_tenant_documents = MagicMock(
        return_value=documents,
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}",
        )

        assert response.status_code == 200
        assert len(response.json()) == 2

        document_service.list_tenant_documents.assert_called_once_with(
            ANY,
            tenant_id,
        )

    finally:
        document_service.list_tenant_documents = original_list
        clear_authentication_override()

def test_list_documents_filters_by_status():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    documents = [
        MagicMock(
            id=uuid4(),
            tenant_id=tenant_id,
            uploaded_by=uuid4(),
            filename="processing.pdf",
            storage_path="documents/processing.pdf",
            status=DocumentStatus.PROCESSING,
        ),
    ]

    original_list = (
        document_service.list_tenant_documents_by_status
    )

    document_service.list_tenant_documents_by_status = MagicMock(
        return_value=documents,
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}",
            params={"status": "processing"},
        )

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["status"] == "processing"

        document_service.list_tenant_documents_by_status.assert_called_once_with(
            ANY,
            tenant_id,
            DocumentStatus.PROCESSING,
        )

    finally:
        document_service.list_tenant_documents_by_status = (
            original_list
        )
        clear_authentication_override()

def test_list_documents_filters_ready_documents():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    documents = [
        MagicMock(
            id=uuid4(),
            tenant_id=tenant_id,
            uploaded_by=uuid4(),
            filename="ready.pdf",
            storage_path="documents/ready.pdf",
            status=DocumentStatus.READY,
        ),
    ]

    original_list = (
        document_service.list_tenant_documents_by_status
    )

    document_service.list_tenant_documents_by_status = MagicMock(
        return_value=documents,
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}",
            params={"status": "ready"},
        )

        assert response.status_code == 200
        assert response.json()[0]["status"] == "ready"

        document_service.list_tenant_documents_by_status.assert_called_once_with(
            ANY,
            tenant_id,
            DocumentStatus.READY,
        )

    finally:
        document_service.list_tenant_documents_by_status = (
            original_list
        )
        clear_authentication_override()

def test_list_documents_filters_failed_documents():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    documents = [
        MagicMock(
            id=uuid4(),
            tenant_id=tenant_id,
            uploaded_by=uuid4(),
            filename="failed.pdf",
            storage_path="documents/failed.pdf",
            status=DocumentStatus.FAILED,
        ),
    ]

    original_list = (
        document_service.list_tenant_documents_by_status
    )

    document_service.list_tenant_documents_by_status = MagicMock(
        return_value=documents,
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}",
            params={"status": "failed"},
        )

        assert response.status_code == 200
        assert response.json()[0]["status"] == "failed"

        document_service.list_tenant_documents_by_status.assert_called_once_with(
            ANY,
            tenant_id,
            DocumentStatus.FAILED,
        )

    finally:
        document_service.list_tenant_documents_by_status = (
            original_list
        )
        clear_authentication_override()

def test_list_documents_requires_authentication():
    tenant_id = uuid4()

    response = client.get(
        f"/documents/{tenant_id}",
    )

    assert response.status_code == 401

def test_list_documents_other_tenant_forbidden():
    own_tenant_id = uuid4()
    other_tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=own_tenant_id,
    )

    try:
        response = client.get(
            f"/documents/{other_tenant_id}",
            params={"status": "processing"},
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()

def test_list_documents_invalid_status_returns_422():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}",
            params={"status": "invalid"},
        )

        assert response.status_code == 422

    finally:
        clear_authentication_override()

def test_upload_document_requires_authentication():
    tenant_id = uuid4()

    response = client.post(
        f"/documents/{tenant_id}/upload",
        files={
            "file": (
                "knowledge.pdf",
                b"pdf-content",
                "application/pdf",
            ),
        },
    )

    assert response.status_code == 401


def test_upload_document_tenant_admin_own_tenant():
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
    document.storage_path = (
        f"{tenant_id}/knowledge.pdf"
    )
    document.status = DocumentStatus.UPLOADED

    original_service = (
        document_service.create_document_from_upload
    )

    document_service.create_document_from_upload = (
        MagicMock(
            return_value=document,
        )
    )

    try:
        response = client.post(
            f"/documents/{tenant_id}/upload",
            files={
                "file": (
                    "knowledge.pdf",
                    b"pdf-content",
                    "application/pdf",
                ),
            },
        )

        assert response.status_code == 201

        document_service.create_document_from_upload.assert_called_once_with(
            ANY,
            tenant_id=tenant_id,
            uploaded_by=user.id,
            filename="knowledge.pdf",
            content=b"pdf-content",
        )

        assert (
            response.json()["filename"]
            == "knowledge.pdf"
        )

    finally:
        document_service.create_document_from_upload = (
            original_service
        )
        clear_authentication_override()


def test_upload_document_tenant_admin_other_tenant():
    user_tenant_id = uuid4()
    requested_tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=user_tenant_id,
    )

    try:
        response = client.post(
            f"/documents/{requested_tenant_id}/upload",
            files={
                "file": (
                    "knowledge.pdf",
                    b"pdf-content",
                    "application/pdf",
                ),
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_upload_document_sub_user_reaches_service():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    original_service = (
        document_service.create_document_from_upload
    )

    document_service.create_document_from_upload = (
        MagicMock(
            side_effect=ValueError(
                "User does not have permission to upload documents."
            ),
        )
    )

    try:
        response = client.post(
            f"/documents/{tenant_id}/upload",
            files={
                "file": (
                    "knowledge.pdf",
                    b"pdf-content",
                    "application/pdf",
                ),
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "User does not have permission to upload documents."
        )

    finally:
        document_service.create_document_from_upload = (
            original_service
        )
        clear_authentication_override()


def test_upload_document_rejects_empty_file():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    try:
        response = client.post(
            f"/documents/{tenant_id}/upload",
            files={
                "file": (
                    "empty.pdf",
                    b"",
                    "application/pdf",
                ),
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Uploaded file cannot be empty."
        )

    finally:
        clear_authentication_override()


def test_download_document_requires_authentication():
    tenant_id = uuid4()
    document_id = uuid4()

    response = client.get(
        f"/documents/{tenant_id}/{document_id}/download",
    )

    assert response.status_code == 401


def test_download_document_tenant_admin_own_tenant():
    tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    document = MagicMock()
    document.id = document_id
    document.tenant_id = tenant_id
    document.uploaded_by = uuid4()
    document.filename = "knowledge.pdf"
    document.storage_path = (
        f"{tenant_id}/knowledge.pdf"
    )
    document.status = DocumentStatus.UPLOADED

    original_service = (
        document_service.get_document_file
    )

    document_service.get_document_file = (
        MagicMock(
            return_value=(
                document,
                Path(__file__),
            ),
        )
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}/{document_id}/download",
        )

        assert response.status_code == 200
        assert (
            response.headers["content-disposition"]
            == 'attachment; filename="knowledge.pdf"'
        )

    finally:
        document_service.get_document_file = (
            original_service
        )
        clear_authentication_override()


def test_download_document_sub_user_own_tenant():
    tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    document = MagicMock()
    document.id = document_id
    document.tenant_id = tenant_id
    document.uploaded_by = uuid4()
    document.filename = "knowledge.pdf"
    document.storage_path = (
        f"{tenant_id}/knowledge.pdf"
    )
    document.status = DocumentStatus.UPLOADED

    original_service = (
        document_service.get_document_file
    )

    document_service.get_document_file = (
        MagicMock(
            return_value=(
                document,
                Path(__file__),
            ),
        )
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}/{document_id}/download",
        )

        assert response.status_code == 200

    finally:
        document_service.get_document_file = (
            original_service
        )
        clear_authentication_override()


def test_download_document_other_tenant_is_forbidden():
    user_tenant_id = uuid4()
    requested_tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=user_tenant_id,
    )

    try:
        response = client.get(
            f"/documents/{requested_tenant_id}/{document_id}/download",
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_download_document_not_found():
    tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    original_service = (
        document_service.get_document_file
    )

    document_service.get_document_file = (
        MagicMock(
            return_value=None,
        )
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}/{document_id}/download",
        )

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Document not found."
        )

    finally:
        document_service.get_document_file = (
            original_service
        )
        clear_authentication_override()


def test_download_document_file_missing():
    tenant_id = uuid4()
    document_id = uuid4()

    authenticate_as(
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    original_service = (
        document_service.get_document_file
    )

    document_service.get_document_file = (
        MagicMock(
            side_effect=FileNotFoundError(
                "Document file not found."
            ),
        )
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}/{document_id}/download",
        )

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Document file not found."
        )

    finally:
        document_service.get_document_file = (
            original_service
        )
        clear_authentication_override()