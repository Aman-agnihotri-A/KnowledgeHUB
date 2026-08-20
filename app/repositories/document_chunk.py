import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.enums import DocumentStatus


class DocumentChunkRepository:
    def delete_by_document(
        self,
        db: Session,
        document_id: uuid.UUID,
    ) -> None:
        db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id
                == document_id
            )
        )

    def create_many(
        self,
        db: Session,
        *,
        document_id: uuid.UUID,
        chunks: list[str],
    ) -> list[DocumentChunk]:
        documents = [
            DocumentChunk(
                document_id=document_id,
                chunk_index=index,
                content=content,
            )
            for index, content in enumerate(
                chunks
            )
        ]

        if documents:
            db.add_all(documents)

        db.flush()

        return documents

    def update_embeddings(
        self,
        db: Session,
        embeddings: dict[
            uuid.UUID,
            list[float],
        ],
    ) -> None:
        if not embeddings:
            return

        chunks = list(
            db.scalars(
                select(DocumentChunk).where(
                    DocumentChunk.id.in_(
                        list(embeddings.keys())
                    )
                )
            ).all()
        )

        for chunk in chunks:
            chunk.embedding = embeddings[
                chunk.id
            ]

        db.flush()

    def list_by_document(
        self,
        db: Session,
        document_id: uuid.UUID,
    ) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id
                == document_id
            )
            .order_by(
                DocumentChunk.chunk_index.asc()
            )
        )

        return list(
            db.scalars(statement).all()
        )

    def list_ready_chunks_by_tenant(
        self,
        db: Session,
        tenant_id: uuid.UUID,
    ) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .join(
                Document,
                Document.id
                == DocumentChunk.document_id,
            )
            .where(
                Document.tenant_id == tenant_id,
                Document.status
                == DocumentStatus.READY,
                DocumentChunk.embedding.is_not(None),
            )
            .order_by(
                DocumentChunk.document_id.asc(),
                DocumentChunk.chunk_index.asc(),
            )
        )

        return list(
            db.scalars(statement).all()
        )