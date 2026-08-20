from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.document import Document
from app.models.enums import DocumentStatus
from app.services.document import DocumentService


def create_document(
    *,
    tenant_id,
    document_id,
    status=DocumentStatus.UPLOADED,
):
    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="tenant-1/knowledge.pdf",
        status=status,
    )

    document.id = document_id

    return document


def test_process_document_creates_chunks_and_marks_ready(
    tmp_path: Path,
):
    db = MagicMock()

    tenant_id = uuid4()
    document_id = uuid4()

    document = create_document(
        tenant_id=tenant_id,
        document_id=document_id,
    )

    storage = MagicMock()
    storage_path = tmp_path / "knowledge.pdf"
    storage_path.write_bytes(
        b"fake pdf content"
    )

    storage.open.return_value = storage_path

    text_service = MagicMock()
    text_service.extract_text.return_value = (
        "KnowledgeHub extracted text"
    )

    chunking_service = MagicMock()
    chunking_service.split.return_value = [
        "KnowledgeHub",
        "extracted text",
    ]

    document_repository = MagicMock()
    document_repository.get_by_id.return_value = (
        document
    )

    def update_status(
        db,
        document,
        status,
    ):
        document.status = status
        return document

    document_repository.update_status.side_effect = (
        update_status
    )

    chunk_repository = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        storage_service=storage,
        document_chunk_repository=chunk_repository,
        document_text_service=text_service,
        chunking_service=chunking_service,
    )

    result = service.process_document(
        db,
        document_id=document_id,
        tenant_id=tenant_id,
    )

    assert result is document
    assert document.status == DocumentStatus.READY

    storage.open.assert_called_once_with(
        document.storage_path
    )

    text_service.extract_text.assert_called_once_with(
        content=b"fake pdf content",
        filename="knowledge.pdf",
    )

    chunking_service.split.assert_called_once_with(
        "KnowledgeHub extracted text"
    )

    chunk_repository.delete_by_document.assert_called_once_with(
        db,
        document_id,
    )

    chunk_repository.create_many.assert_called_once_with(
        db,
        document_id=document_id,
        chunks=[
            "KnowledgeHub",
            "extracted text",
        ],
    )


def test_process_document_rejects_cross_tenant_document():
    db = MagicMock()

    tenant_id = uuid4()
    other_tenant_id = uuid4()
    document_id = uuid4()

    document = create_document(
        tenant_id=other_tenant_id,
        document_id=document_id,
    )

    document_repository = MagicMock()
    document_repository.get_by_id.return_value = (
        document
    )

    service = DocumentService(
        document_repository=document_repository,
        storage_service=MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="Document not found.",
    ):
        service.process_document(
            db,
            document_id=document_id,
            tenant_id=tenant_id,
        )

    document_repository.update_status.assert_not_called()


def test_process_document_returns_ready_document_without_reprocessing():
    db = MagicMock()

    tenant_id = uuid4()
    document_id = uuid4()

    document = create_document(
        tenant_id=tenant_id,
        document_id=document_id,
        status=DocumentStatus.READY,
    )

    document_repository = MagicMock()
    document_repository.get_by_id.return_value = (
        document
    )

    storage = MagicMock()

    service = DocumentService(
        document_repository=document_repository,
        storage_service=storage,
    )

    result = service.process_document(
        db,
        document_id=document_id,
        tenant_id=tenant_id,
    )

    assert result is document
    storage.open.assert_not_called()


def test_process_document_marks_failed_when_extraction_fails(
    tmp_path: Path,
):
    db = MagicMock()

    tenant_id = uuid4()
    document_id = uuid4()

    document = create_document(
        tenant_id=tenant_id,
        document_id=document_id,
    )

    storage_path = tmp_path / "knowledge.pdf"
    storage_path.write_bytes(
        b"invalid pdf"
    )

    storage = MagicMock()
    storage.open.return_value = storage_path

    text_service = MagicMock()
    text_service.extract_text.side_effect = (
        ValueError("Invalid PDF document.")
    )

    document_repository = MagicMock()
    document_repository.get_by_id.return_value = (
        document
    )

    def update_status(
        db,
        document,
        status,
    ):
        document.status = status
        return document

    document_repository.update_status.side_effect = (
        update_status
    )

    service = DocumentService(
        document_repository=document_repository,
        storage_service=storage,
        document_text_service=text_service,
    )

    with pytest.raises(
        ValueError,
        match="Invalid PDF document.",
    ):
        service.process_document(
            db,
            document_id=document_id,
            tenant_id=tenant_id,
        )

    assert document.status == DocumentStatus.FAILED