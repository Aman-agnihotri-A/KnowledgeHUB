import uuid

from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.enums import DocumentStatus, UserRole
from app.repositories.document import DocumentRepository
from app.repositories.user import UserRepository
from app.services.storage import StorageService


class DocumentService:
    def __init__(
        self,
        document_repository: DocumentRepository | None = None,
        user_repository: UserRepository | None = None,
        storage_service: StorageService | None = None,
    ) -> None:
        self.document_repository = (
            document_repository or DocumentRepository()
        )

        self.user_repository = (
            user_repository or UserRepository()
        )

        self.storage_service = storage_service

    def create_document(
        self,
        db: Session,
        *,
        tenant_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        filename: str,
        storage_path: str,
    ) -> Document:
        uploader = self.user_repository.get_by_id(
            db,
            uploaded_by,
        )

        if uploader is None:
            raise ValueError(
                f"User '{uploaded_by}' does not exist."
            )

        if uploader.tenant_id != tenant_id:
            raise ValueError(
                "User does not belong to the specified tenant."
            )

        if uploader.role not in {
            UserRole.SUPER_ADMIN,
            UserRole.TENANT_ADMIN,
        }:
            raise ValueError(
                "User does not have permission to upload documents."
            )

        return self.document_repository.create(
            db,
            tenant_id=tenant_id,
            uploaded_by=uploaded_by,
            filename=filename,
            storage_path=storage_path,
        )

    def create_document_from_upload(
        self,
        db: Session,
        *,
        tenant_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        filename: str,
        content: bytes,
    ) -> Document:
        if self.storage_service is None:
            raise ValueError(
                "Document storage is not configured."
            )

        uploader = self.user_repository.get_by_id(
            db,
            uploaded_by,
        )

        if uploader is None:
            raise ValueError(
                f"User '{uploaded_by}' does not exist."
            )

        if uploader.tenant_id != tenant_id:
            raise ValueError(
                "User does not belong to the specified tenant."
            )

        if uploader.role not in {
            UserRole.SUPER_ADMIN,
            UserRole.TENANT_ADMIN,
        }:
            raise ValueError(
                "User does not have permission to upload documents."
            )

        storage_path = self.storage_service.save(
            tenant_id=str(tenant_id),
            filename=filename,
            content=content,
        )

        try:
            return self.document_repository.create(
                db,
                tenant_id=tenant_id,
                uploaded_by=uploaded_by,
                filename=filename,
                storage_path=storage_path,
            )
        except Exception:
            self.storage_service.delete(
                storage_path,
            )
            raise

    def get_document(
        self,
        db: Session,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> Document | None:
        document = self.document_repository.get_by_id(
            db,
            document_id,
        )

        if document is None:
            return None

        if document.tenant_id != tenant_id:
            return None

        return document

    def get_document_file(
        self,
        db: Session,
        *,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> tuple[Document, Path] | None:
        if self.storage_service is None:
            raise ValueError(
                "Document storage is not configured."
            )

        document = self.get_document(
            db,
            document_id,
            tenant_id,
        )

        if document is None:
            return None

        path = self.storage_service.open(
            document.storage_path,
        )

        if path is None:
            raise FileNotFoundError(
                "Document file not found."
            )

        return document, path

    def list_tenant_documents(
        self,
        db: Session,
        tenant_id: uuid.UUID,
    ) -> list[Document]:
        return self.document_repository.list_by_tenant(
            db,
            tenant_id,
        )

    def list_tenant_documents_by_status(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        status: DocumentStatus,
    ) -> list[Document]:
        return self.document_repository.list_by_tenant_and_status(
            db,
            tenant_id,
            status,
        )

    def update_document_status(
        self,
        db: Session,
        *,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        status: DocumentStatus,
    ) -> Document:
        document = self.document_repository.get_by_id(
            db,
            document_id,
        )

        if document is None:
            raise ValueError(
                "Document not found."
            )

        if document.tenant_id != tenant_id:
            raise ValueError(
                "Document does not belong to the specified tenant."
            )

        allowed_transitions: dict[
            DocumentStatus,
            set[DocumentStatus],
        ] = {
            DocumentStatus.UPLOADED: {
                DocumentStatus.PROCESSING,
                DocumentStatus.FAILED,
            },
            DocumentStatus.PROCESSING: {
                DocumentStatus.READY,
                DocumentStatus.FAILED,
            },
            DocumentStatus.READY: set(),
            DocumentStatus.FAILED: {
                DocumentStatus.PROCESSING,
            },
        }

        current_status = document.status

        if status == current_status:
            return document

        if status not in allowed_transitions[current_status]:
            raise ValueError(
                f"Invalid document status transition: "
                f"{current_status.value} -> {status.value}."
            )

        return self.document_repository.update_status(
            db,
            document,
            status,
        )