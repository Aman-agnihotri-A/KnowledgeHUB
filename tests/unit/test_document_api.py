from uuid import uuid4
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.api.documents import document_service


client = TestClient(app)


def test_create_document():
    tenant_id = uuid4()
    user_id = uuid4()
    document_id = uuid4()

    document = MagicMock()
    document.id = document_id
    document.tenant_id = tenant_id
    document.uploaded_by = user_id
    document.filename = "knowledge.pdf"
    document.storage_path = "documents/knowledge.pdf"
    document.status = "UPLOADED"

    original_service = document_service.create_document
    document_service.create_document = MagicMock(
        return_value=document
    )

    try:
        response = client.post(
            f"/documents/{tenant_id}",
            params={"uploaded_by": str(user_id)},
            json={
                "filename": "knowledge.pdf",
                "storage_path": "documents/knowledge.pdf",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["id"] == str(document_id)
        assert data["tenant_id"] == str(tenant_id)
        assert data["uploaded_by"] == str(user_id)
        assert data["filename"] == "knowledge.pdf"

    finally:
        document_service.create_document = original_service


def test_get_document_not_found():
    tenant_id = uuid4()
    document_id = uuid4()

    original_service = document_service.get_document
    document_service.get_document = MagicMock(
        return_value=None
    )

    try:
        response = client.get(
            f"/documents/{tenant_id}/{document_id}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Document not found."

    finally:
        document_service.get_document = original_service