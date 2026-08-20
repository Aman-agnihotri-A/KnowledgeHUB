import math
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.repositories.document_chunk import (
    DocumentChunkRepository,
)
from app.services.embedding import (
    DeterministicEmbeddingService,
    EmbeddingService,
)


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: DocumentChunk
    similarity: float


class RetrievalService:
    """
    Tenant-safe semantic retrieval over persisted chunk
    embeddings.

    The current storage model uses JSON embeddings, so
    similarity is calculated in application code. This
    keeps KH-031 independent of a vector-database or
    PostgreSQL vector extension.
    """

    def __init__(
        self,
        document_chunk_repository: (
            DocumentChunkRepository | None
        ) = None,
        embedding_service: (
            EmbeddingService | None
        ) = None,
    ) -> None:
        self.document_chunk_repository = (
            document_chunk_repository
            or DocumentChunkRepository()
        )

        self.embedding_service = (
            embedding_service
            or DeterministicEmbeddingService()
        )

    def retrieve(
        self,
        db: Session,
        *,
        tenant_id: uuid.UUID,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        normalized_query = query.strip()

        if not normalized_query:
            raise ValueError(
                "Query cannot be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        query_embedding = (
            self.embedding_service.embed(
                normalized_query,
            )
        )

        self._validate_embedding(
            query_embedding,
        )

        chunks = (
            self.document_chunk_repository
            .list_ready_chunks_by_tenant(
                db,
                tenant_id,
            )
        )

        scored_chunks: list[RetrievedChunk] = []

        for chunk in chunks:
            if chunk.embedding is None:
                continue

            chunk_embedding = [
                float(value)
                for value in chunk.embedding
            ]

            self._validate_embedding(
                chunk_embedding,
            )

            similarity = self.cosine_similarity(
                query_embedding,
                chunk_embedding,
            )

            scored_chunks.append(
                RetrievedChunk(
                    chunk=chunk,
                    similarity=similarity,
                )
            )

        scored_chunks.sort(
            key=lambda item: (
                item.similarity,
                -item.chunk.chunk_index,
            ),
            reverse=True,
        )

        return scored_chunks[:top_k]

    def _validate_embedding(
        self,
        embedding: list[float],
    ) -> None:
        if len(embedding) != (
            self.embedding_service.dimensions
        ):
            raise ValueError(
                "Embedding dimension does not match "
                "the configured embedding service."
            )

        if not all(
            isinstance(
                value,
                (int, float),
            )
            and math.isfinite(float(value))
            for value in embedding
        ):
            raise ValueError(
                "Embedding values must be finite numeric values."
            )

    @staticmethod
    def cosine_similarity(
        first: list[float],
        second: list[float],
    ) -> float:
        if len(first) != len(second):
            raise ValueError(
                "Embeddings must have the same dimensions."
            )

        first_norm = math.sqrt(
            sum(
                value * value
                for value in first
            )
        )

        second_norm = math.sqrt(
            sum(
                value * value
                for value in second
            )
        )

        if first_norm == 0 or second_norm == 0:
            return 0.0

        dot_product = sum(
            first_value * second_value
            for first_value, second_value in zip(
                first,
                second,
            )
        )

        return dot_product / (
            first_norm * second_norm
        )