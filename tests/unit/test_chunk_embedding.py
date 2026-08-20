from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.document_chunk import (
    DocumentChunk,
)
from app.services.chunk_embedding import (
    ChunkEmbeddingService,
)


def create_chunk(
    content: str,
) -> DocumentChunk:
    chunk = DocumentChunk(
        document_id=uuid4(),
        chunk_index=0,
        content=content,
    )

    chunk.id = uuid4()

    return chunk


def test_embed_chunk():
    embedding_service = MagicMock()

    embedding_service.dimensions = 3

    embedding_service.embed.return_value = [
        0.1,
        0.2,
        0.3,
    ]

    service = ChunkEmbeddingService(
        embedding_service,
    )

    chunk = create_chunk(
        "KnowledgeHub",
    )

    result = service.embed_chunk(
        chunk,
    )

    assert result == [
        0.1,
        0.2,
        0.3,
    ]

    embedding_service.embed.assert_called_once_with(
        "KnowledgeHub",
    )


def test_embed_chunks():
    embedding_service = MagicMock()

    embedding_service.dimensions = 3

    embedding_service.embed.side_effect = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]

    service = ChunkEmbeddingService(
        embedding_service,
    )

    first = create_chunk(
        "First chunk",
    )

    second = create_chunk(
        "Second chunk",
    )

    result = service.embed_chunks(
        [first, second],
    )

    assert result == {
        first.id: [
            0.1,
            0.2,
            0.3,
        ],
        second.id: [
            0.4,
            0.5,
            0.6,
        ],
    }


def test_empty_chunk_is_rejected():
    embedding_service = MagicMock()
    embedding_service.dimensions = 3

    service = ChunkEmbeddingService(
        embedding_service,
    )

    chunk = create_chunk("   ")

    with pytest.raises(
        ValueError,
        match="empty document chunk",
    ):
        service.embed_chunk(chunk)


def test_embedding_dimension_is_validated():
    embedding_service = MagicMock()

    embedding_service.dimensions = 3

    embedding_service.embed.return_value = [
        0.1,
        0.2,
    ]

    service = ChunkEmbeddingService(
        embedding_service,
    )

    chunk = create_chunk(
        "KnowledgeHub",
    )

    with pytest.raises(
        ValueError,
        match="Embedding dimension",
    ):
        service.embed_chunk(chunk)


def test_non_numeric_embedding_is_rejected():
    embedding_service = MagicMock()

    embedding_service.dimensions = 2

    embedding_service.embed.return_value = [
        0.1,
        "invalid",
    ]

    service = ChunkEmbeddingService(
        embedding_service,
    )

    chunk = create_chunk(
        "KnowledgeHub",
    )

    with pytest.raises(
        ValueError,
        match="numeric",
    ):
        service.embed_chunk(chunk)