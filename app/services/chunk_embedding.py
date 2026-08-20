import uuid

from app.models.document_chunk import (
    DocumentChunk,
)
from app.services.embedding import (
    EmbeddingService,
)


class ChunkEmbeddingService:
    """Generate and validate embeddings for document chunks."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
    ) -> None:
        self.embedding_service = (
            embedding_service
        )

    def embed_chunk(
        self,
        chunk: DocumentChunk,
    ) -> list[float]:
        if not chunk.content.strip():
            raise ValueError(
                "Cannot embed an empty document chunk."
            )

        embedding = (
            self.embedding_service.embed(
                chunk.content,
            )
        )

        self._validate_embedding(
            embedding,
        )

        return embedding

    def embed_chunks(
        self,
        chunks: list[DocumentChunk],
    ) -> dict[uuid.UUID, list[float]]:
        embeddings: dict[
            uuid.UUID,
            list[float],
        ] = {}

        for chunk in chunks:
            embeddings[chunk.id] = (
                self.embed_chunk(chunk)
            )

        return embeddings

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
            for value in embedding
        ):
            raise ValueError(
                "Embedding values must be numeric."
            )