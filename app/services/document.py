import uuid

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.repositories.user import UserRepository


class DocumentService:
    def __init__(
        self,
        document_repository: DocumentRepository | None = None,
        user_repository: UserRepository | None = None,
    ) -> None:
        self.document_repository = (
            document_repository or DocumentRepository()
        )
        self.user_repository = (
            user_repository or UserRepository()
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

    def list_tenant_documents(
        self,
        db: Session,
        tenant_id: uuid.UUID,
    ) -> list[Document]:
        return self.document_repository.list_by_tenant(
            db,
            tenant_id,
        )