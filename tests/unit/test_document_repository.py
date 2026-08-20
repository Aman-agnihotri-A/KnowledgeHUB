from unittest.mock import MagicMock
from uuid import uuid4

from app.models.document import Document
from app.models.enums import DocumentStatus
from app.repositories.document import DocumentRepository


def test_create_document():
    db = MagicMock()
    repository = DocumentRepository()

    tenant_id = uuid4()
    uploaded_by = uuid4()

    document = repository.create(
        db,
        tenant_id=tenant_id,
        uploaded_by=uploaded_by,
        filename="knowledge.pdf",
        storage_path="tenants/acme/knowledge.pdf",
    )

    assert document.tenant_id == tenant_id
    assert document.uploaded_by == uploaded_by
    assert document.filename == "knowledge.pdf"
    assert document.storage_path == "tenants/acme/knowledge.pdf"
    assert document.status == DocumentStatus.UPLOADED

    db.add.assert_called_once_with(document)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(document)


def test_get_document_by_id():
    db = MagicMock()
    repository = DocumentRepository()

    document_id = uuid4()

    document = Document(
        tenant_id=uuid4(),
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
    )

    db.scalar.return_value = document

    result = repository.get_by_id(
        db,
        document_id,
    )

    assert result is document
    db.scalar.assert_called_once()


def test_list_documents_by_tenant():
    db = MagicMock()
    repository = DocumentRepository()

    tenant_id = uuid4()

    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
    )

    db.scalars.return_value.all.return_value = [document]

    result = repository.list_by_tenant(
        db,
        tenant_id,
    )

    assert result == [document]


def test_list_documents_by_tenant_and_status():
    db = MagicMock()
    repository = DocumentRepository()

    tenant_id = uuid4()

    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
        status=DocumentStatus.READY,
    )

    db.scalars.return_value.all.return_value = [document]

    result = repository.list_by_tenant_and_status(
        db,
        tenant_id,
        DocumentStatus.READY,
    )

    assert result == [document]


def test_update_document_status():
    db = MagicMock()
    repository = DocumentRepository()

    document = Document(
        tenant_id=uuid4(),
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
        status=DocumentStatus.UPLOADED,
    )

    result = repository.update_status(
        db,
        document,
        DocumentStatus.PROCESSING,
    )

    assert result is document
    assert document.status == DocumentStatus.PROCESSING

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(document)

def test_update_document_status_to_failed():
    db = MagicMock()
    repository = DocumentRepository()

    document = Document(
        tenant_id=uuid4(),
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
        status=DocumentStatus.PROCESSING,
    )

    result = repository.update_status(
        db,
        document,
        DocumentStatus.FAILED,
    )

    assert result is document
    assert document.status == DocumentStatus.FAILED

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(document)

def test_list_documents_by_tenant_and_status():
    db = MagicMock()
    repository = DocumentRepository()

    tenant_id = uuid4()

    documents = [
        Document(
            tenant_id=tenant_id,
            uploaded_by=uuid4(),
            filename="processing-1.pdf",
            storage_path="documents/processing-1.pdf",
            status=DocumentStatus.PROCESSING,
        ),
        Document(
            tenant_id=tenant_id,
            uploaded_by=uuid4(),
            filename="processing-2.pdf",
            storage_path="documents/processing-2.pdf",
            status=DocumentStatus.PROCESSING,
        ),
    ]

    db.scalars.return_value.all.return_value = documents

    result = repository.list_by_tenant_and_status(
        db,
        tenant_id,
        DocumentStatus.PROCESSING,
    )

    assert result == documents
    db.scalars.assert_called_once()