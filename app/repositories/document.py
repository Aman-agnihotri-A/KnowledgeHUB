import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.enums import DocumentStatus


class DocumentRepository:
    def create(
        self,
        db: Session,
        *,
        tenant_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        filename: str,
        storage_path: str,
        status: DocumentStatus = DocumentStatus.UPLOADED,
    ) -> Document:
        document = Document(
            tenant_id=tenant_id,
            uploaded_by=uploaded_by,
            filename=filename,
            storage_path=storage_path,
            status=status,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    def get_by_id(
        self,
        db: Session,
        document_id: uuid.UUID,
    ) -> Document | None:
        statement = select(Document).where(
            Document.id == document_id
        )

        return db.scalar(statement)

    def list_by_tenant(
        self,
        db: Session,
        tenant_id: uuid.UUID,
    ) -> list[Document]:
        statement = (
            select(Document)
            .where(Document.tenant_id == tenant_id)
            .order_by(Document.created_at.desc())
        )

        return list(db.scalars(statement).all())

    def list_by_tenant_and_status(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        status: DocumentStatus,
    ) -> list[Document]:
        statement = (
            select(Document)
            .where(
                Document.tenant_id == tenant_id,
                Document.status == status,
            )
            .order_by(Document.created_at.desc())
        )

        return list(db.scalars(statement).all())

    def update_status(
        self,
        db: Session,
        document: Document,
        status: DocumentStatus,
    ) -> Document:
        document.status = status

        db.commit()
        db.refresh(document)

        return document

    def delete(
        self,
        db: Session,
        document: Document,
    ) -> None:
        db.delete(document)
        db.commit()