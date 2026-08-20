import uuid

from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.enums import DocumentStatus, UserRole
from app.repositories.document import DocumentRepository
from app.repositories.document_chunk import (
    DocumentChunkRepository,
)
from app.repositories.user import UserRepository
from app.services.chunking import TextChunkingService
from app.services.document_text import DocumentTextService
from app.services.storage import StorageService
from app.services.chunk_embedding import (
    ChunkEmbeddingService,
)
from app.services.embedding import (
    DeterministicEmbeddingService,
    EmbeddingService,
)


class DocumentService:
    def __init__(
        self,
        document_repository: DocumentRepository | None = None,
        user_repository: UserRepository | None = None,
        storage_service: StorageService | None = None,
        document_chunk_repository: (
            DocumentChunkRepository | None
        ) = None,
        document_text_service: (
            DocumentTextService | None
        ) = None,
        chunking_service: (
            TextChunkingService | None
        ) = None,
        embedding_service: (
            EmbeddingService | None
        ) = None,
    ) -> None:
        self.document_repository = (
            document_repository
            or DocumentRepository()
        )

        self.user_repository = (
            user_repository
            or UserRepository()
        )

        self.storage_service = storage_service

        self.document_chunk_repository = (
            document_chunk_repository
            or DocumentChunkRepository()
        )

        self.document_text_service = (
            document_text_service
            or DocumentTextService()
        )

        self.chunking_service = (
            chunking_service
            or TextChunkingService()
        )

        self.embedding_service = (
            embedding_service
            or DeterministicEmbeddingService()
        )

        self.chunk_embedding_service = (
            ChunkEmbeddingService(
                self.embedding_service
            )
        )

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
        return (
            self.document_repository
            .list_by_tenant_and_status(
                db,
                tenant_id,
                status,
            )
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

    def process_document(
        self,
        db: Session,
        *,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> Document:
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
            raise ValueError(
                "Document not found."
            )

        if document.status == DocumentStatus.READY:
            return document

        path = self.storage_service.open(
            document.storage_path,
        )

        if path is None:
            raise FileNotFoundError(
                "Document file not found."
            )

        self.document_repository.update_status(
            db,
            document,
            DocumentStatus.PROCESSING,
        )

        try:
            content = path.read_bytes()

            text = self.document_text_service.extract_text(
                content=content,
                filename=document.filename,
            )

            chunks = self.chunking_service.split(
                text,
            )

            if not chunks:
                raise ValueError(
                    "Document produced no text chunks."
                )

            self.document_chunk_repository.delete_by_document(
                db,
                document.id,
            )

            created_chunks = (
                self.document_chunk_repository.create_many(
                    db,
                    document_id=document.id,
                    chunks=chunks,
                )
            )

            embeddings = (
                self.chunk_embedding_service.embed_chunks(
                    created_chunks,
                )
            )

            self.document_chunk_repository.update_embeddings(
                db,
                embeddings,
            )

            return self.document_repository.update_status(
                db,
                document,
                DocumentStatus.READY,
            )

        except Exception:
            self.document_repository.update_status(
                db,
                document,
                DocumentStatus.FAILED,
            )
            raise