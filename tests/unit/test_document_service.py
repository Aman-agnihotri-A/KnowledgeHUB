from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.document import Document
from app.models.enums import DocumentStatus, UserRole
from app.models.user import User
from app.services.document import DocumentService


def test_create_document():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()
    user_id = uuid4()

    uploader = User(
        email="admin@example.com",
        hashed_password="hashed-password",
        full_name="Tenant Admin",
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant_id,
    )

    document = Document(
        tenant_id=tenant_id,
        uploaded_by=user_id,
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
    )

    user_repository.get_by_id.return_value = uploader
    document_repository.create.return_value = document

    result = service.create_document(
        db,
        tenant_id=tenant_id,
        uploaded_by=user_id,
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
    )

    assert result is document

    user_repository.get_by_id.assert_called_once_with(
        db,
        user_id,
    )

    document_repository.create.assert_called_once_with(
        db,
        tenant_id=tenant_id,
        uploaded_by=user_id,
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
    )


def test_create_document_rejects_unknown_uploader():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()
    user_id = uuid4()

    user_repository.get_by_id.return_value = None

    with pytest.raises(
        ValueError,
        match=f"User '{user_id}' does not exist.",
    ):
        service.create_document(
            db,
            tenant_id=tenant_id,
            uploaded_by=user_id,
            filename="knowledge.pdf",
            storage_path="documents/knowledge.pdf",
        )

    document_repository.create.assert_not_called()


def test_create_document_rejects_cross_tenant_uploader():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()
    other_tenant_id = uuid4()
    user_id = uuid4()

    uploader = User(
        email="admin@example.com",
        hashed_password="hashed-password",
        full_name="Tenant Admin",
        role=UserRole.TENANT_ADMIN,
        tenant_id=other_tenant_id,
    )

    user_repository.get_by_id.return_value = uploader

    with pytest.raises(
        ValueError,
        match="User does not belong to the specified tenant.",
    ):
        service.create_document(
            db,
            tenant_id=tenant_id,
            uploaded_by=user_id,
            filename="knowledge.pdf",
            storage_path="documents/knowledge.pdf",
        )

    document_repository.create.assert_not_called()


def test_sub_user_cannot_upload_document():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()
    user_id = uuid4()

    uploader = User(
        email="user@example.com",
        hashed_password="hashed-password",
        full_name="Sub User",
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    user_repository.get_by_id.return_value = uploader

    with pytest.raises(
        ValueError,
        match="User does not have permission to upload documents.",
    ):
        service.create_document(
            db,
            tenant_id=tenant_id,
            uploaded_by=user_id,
            filename="knowledge.pdf",
            storage_path="documents/knowledge.pdf",
        )

    document_repository.create.assert_not_called()


def test_get_document_returns_tenant_document():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()
    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
    )

    document_repository.get_by_id.return_value = document

    result = service.get_document(
        db,
        document.id,
        tenant_id,
    )

    assert result is document


def test_get_document_hides_other_tenant_document():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()
    other_tenant_id = uuid4()

    document = Document(
        tenant_id=other_tenant_id,
        uploaded_by=uuid4(),
        filename="secret.pdf",
        storage_path="documents/secret.pdf",
    )

    document_repository.get_by_id.return_value = document

    result = service.get_document(
        db,
        document.id,
        tenant_id,
    )

    assert result is None


def test_get_missing_document():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    document_repository.get_by_id.return_value = None

    result = service.get_document(
        db,
        uuid4(),
        uuid4(),
    )

    assert result is None


def test_list_tenant_documents():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()

    documents = [
        Document(
            tenant_id=tenant_id,
            uploaded_by=uuid4(),
            filename="one.pdf",
            storage_path="documents/one.pdf",
        ),
        Document(
            tenant_id=tenant_id,
            uploaded_by=uuid4(),
            filename="two.pdf",
            storage_path="documents/two.pdf",
        ),
    ]

    document_repository.list_by_tenant.return_value = documents

    result = service.list_tenant_documents(
        db,
        tenant_id,
    )

    assert result == documents

    document_repository.list_by_tenant.assert_called_once_with(
        db,
        tenant_id,
    )

def test_update_document_status_uploaded_to_processing():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()

    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
        status=DocumentStatus.UPLOADED,
    )

    document_repository.get_by_id.return_value = document
    document_repository.update_status.return_value = document

    result = service.update_document_status(
        db,
        document_id=document.id,
        tenant_id=tenant_id,
        status=DocumentStatus.PROCESSING,
    )

    assert result is document

    document_repository.get_by_id.assert_called_once_with(
        db,
        document.id,
    )

    document_repository.update_status.assert_called_once_with(
        db,
        document,
        DocumentStatus.PROCESSING,
    )


def test_update_document_status_processing_to_ready():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()

    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
        status=DocumentStatus.PROCESSING,
    )

    document_repository.get_by_id.return_value = document
    document_repository.update_status.return_value = document

    result = service.update_document_status(
        db,
        document_id=document.id,
        tenant_id=tenant_id,
        status=DocumentStatus.READY,
    )

    assert result is document

    document_repository.update_status.assert_called_once_with(
        db,
        document,
        DocumentStatus.READY,
    )


def test_update_document_status_processing_to_failed():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()

    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
        status=DocumentStatus.PROCESSING,
    )

    document_repository.get_by_id.return_value = document
    document_repository.update_status.return_value = document

    result = service.update_document_status(
        db,
        document_id=document.id,
        tenant_id=tenant_id,
        status=DocumentStatus.FAILED,
    )

    assert result is document

    document_repository.update_status.assert_called_once_with(
        db,
        document,
        DocumentStatus.FAILED,
    )


def test_update_document_status_uploaded_to_failed():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()

    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
        status=DocumentStatus.UPLOADED,
    )

    document_repository.get_by_id.return_value = document
    document_repository.update_status.return_value = document

    result = service.update_document_status(
        db,
        document_id=document.id,
        tenant_id=tenant_id,
        status=DocumentStatus.FAILED,
    )

    assert result is document

    document_repository.update_status.assert_called_once_with(
        db,
        document,
        DocumentStatus.FAILED,
    )


def test_update_document_status_failed_to_processing():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()

    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
        status=DocumentStatus.FAILED,
    )

    document_repository.get_by_id.return_value = document
    document_repository.update_status.return_value = document

    result = service.update_document_status(
        db,
        document_id=document.id,
        tenant_id=tenant_id,
        status=DocumentStatus.PROCESSING,
    )

    assert result is document

    document_repository.update_status.assert_called_once_with(
        db,
        document,
        DocumentStatus.PROCESSING,
    )


def test_update_document_status_same_status_is_idempotent():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()

    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
        status=DocumentStatus.PROCESSING,
    )

    document_repository.get_by_id.return_value = document

    result = service.update_document_status(
        db,
        document_id=document.id,
        tenant_id=tenant_id,
        status=DocumentStatus.PROCESSING,
    )

    assert result is document

    document_repository.update_status.assert_not_called()


def test_update_document_status_rejects_uploaded_to_ready():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()

    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
        status=DocumentStatus.UPLOADED,
    )

    document_repository.get_by_id.return_value = document

    with pytest.raises(
        ValueError,
        match=(
            "Invalid document status transition: "
            "uploaded -> ready."
        ),
    ):
        service.update_document_status(
            db,
            document_id=document.id,
            tenant_id=tenant_id,
            status=DocumentStatus.READY,
        )

    document_repository.update_status.assert_not_called()


def test_update_document_status_rejects_ready_to_failed():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()

    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
        status=DocumentStatus.READY,
    )

    document_repository.get_by_id.return_value = document

    with pytest.raises(
        ValueError,
        match=(
            "Invalid document status transition: "
            "ready -> failed."
        ),
    ):
        service.update_document_status(
            db,
            document_id=document.id,
            tenant_id=tenant_id,
            status=DocumentStatus.FAILED,
        )

    document_repository.update_status.assert_not_called()


def test_update_document_status_rejects_ready_to_processing():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    tenant_id = uuid4()

    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
        status=DocumentStatus.READY,
    )

    document_repository.get_by_id.return_value = document

    with pytest.raises(
        ValueError,
        match=(
            "Invalid document status transition: "
            "ready -> processing."
        ),
    ):
        service.update_document_status(
            db,
            document_id=document.id,
            tenant_id=tenant_id,
            status=DocumentStatus.PROCESSING,
        )

    document_repository.update_status.assert_not_called()


def test_update_document_status_rejects_cross_tenant_document():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    document_tenant_id = uuid4()
    requested_tenant_id = uuid4()

    document = Document(
        tenant_id=document_tenant_id,
        uploaded_by=uuid4(),
        filename="secret.pdf",
        storage_path="documents/secret.pdf",
        status=DocumentStatus.UPLOADED,
    )

    document_repository.get_by_id.return_value = document

    with pytest.raises(
        ValueError,
        match="Document does not belong to the specified tenant.",
    ):
        service.update_document_status(
            db,
            document_id=document.id,
            tenant_id=requested_tenant_id,
            status=DocumentStatus.PROCESSING,
        )

    document_repository.update_status.assert_not_called()


def test_update_document_status_rejects_missing_document():
    db = MagicMock()
    document_repository = MagicMock()
    user_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        user_repository=user_repository,
    )

    document_repository.get_by_id.return_value = None

    with pytest.raises(
        ValueError,
        match="Document not found.",
    ):
        service.update_document_status(
            db,
            document_id=uuid4(),
            tenant_id=uuid4(),
            status=DocumentStatus.PROCESSING,
        )

    document_repository.update_status.assert_not_called()