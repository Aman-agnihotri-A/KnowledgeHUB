from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.enums import DocumentStatus
from app.services.retrieval import RetrievalService


def create_chunk(
    *,
    tenant_id,
    content,
    chunk_index,
    embedding,
):
    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="knowledge.pdf",
        storage_path="documents/knowledge.pdf",
        status=DocumentStatus.READY,
    )

    document.id = uuid4()

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=chunk_index,
        content=content,
    )

    chunk.id = uuid4()
    chunk.embedding = embedding
    chunk.document = document

    return chunk


def test_cosine_similarity_identical_vectors():
    result = RetrievalService.cosine_similarity(
        [1.0, 0.0],
        [1.0, 0.0],
    )

    assert result == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    result = RetrievalService.cosine_similarity(
        [1.0, 0.0],
        [0.0, 1.0],
    )

    assert result == pytest.approx(0.0)


def test_cosine_similarity_rejects_dimension_mismatch():
    with pytest.raises(
        ValueError,
        match="same dimensions",
    ):
        RetrievalService.cosine_similarity(
            [1.0, 0.0],
            [1.0],
        )


def test_retrieve_ranks_chunks_by_similarity():
    db = MagicMock()
    repository = MagicMock()
    embedding_service = MagicMock()

    tenant_id = uuid4()

    first = create_chunk(
        tenant_id=tenant_id,
        content="Most relevant",
        chunk_index=0,
        embedding=[1.0, 0.0, 0.0],
    )

    second = create_chunk(
        tenant_id=tenant_id,
        content="Less relevant",
        chunk_index=1,
        embedding=[0.0, 1.0, 0.0],
    )

    third = create_chunk(
        tenant_id=tenant_id,
        content="Moderately relevant",
        chunk_index=2,
        embedding=[0.8, 0.6, 0.0],
    )

    repository.list_ready_chunks_by_tenant.return_value = [
        second,
        third,
        first,
    ]

    embedding_service.dimensions = 3
    embedding_service.embed.return_value = [
        1.0,
        0.0,
        0.0,
    ]

    service = RetrievalService(
        document_chunk_repository=repository,
        embedding_service=embedding_service,
    )

    results = service.retrieve(
        db,
        tenant_id=tenant_id,
        query="knowledge",
        top_k=2,
    )

    assert len(results) == 2
    assert (
        results[0].chunk.content
        == "Most relevant"
    )
    assert (
        results[1].chunk.content
        == "Moderately relevant"
    )

    embedding_service.embed.assert_called_once_with(
        "knowledge",
    )

    repository.list_ready_chunks_by_tenant.assert_called_once_with(
        db,
        tenant_id,
    )


def test_retrieve_respects_top_k():
    db = MagicMock()
    repository = MagicMock()
    embedding_service = MagicMock()

    tenant_id = uuid4()

    chunks = [
        create_chunk(
            tenant_id=tenant_id,
            content=f"Chunk {index}",
            chunk_index=index,
            embedding=[1.0, 0.0],
        )
        for index in range(5)
    ]

    repository.list_ready_chunks_by_tenant.return_value = chunks

    embedding_service.dimensions = 2
    embedding_service.embed.return_value = [
        1.0,
        0.0,
    ]

    service = RetrievalService(
        document_chunk_repository=repository,
        embedding_service=embedding_service,
    )

    results = service.retrieve(
        db,
        tenant_id=tenant_id,
        query="query",
        top_k=3,
    )

    assert len(results) == 3


def test_retrieve_rejects_empty_query():
    db = MagicMock()

    service = RetrievalService(
        document_chunk_repository=MagicMock(),
        embedding_service=MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        service.retrieve(
            db,
            tenant_id=uuid4(),
            query="   ",
        )


def test_retrieve_rejects_invalid_top_k():
    db = MagicMock()

    service = RetrievalService(
        document_chunk_repository=MagicMock(),
        embedding_service=MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="top_k",
    ):
        service.retrieve(
            db,
            tenant_id=uuid4(),
            query="knowledge",
            top_k=0,
        )


def test_retrieve_rejects_query_embedding_dimension_mismatch():
    db = MagicMock()
    embedding_service = MagicMock()

    embedding_service.dimensions = 3
    embedding_service.embed.return_value = [
        0.1,
        0.2,
    ]

    service = RetrievalService(
        document_chunk_repository=MagicMock(),
        embedding_service=embedding_service,
    )

    with pytest.raises(
        ValueError,
        match="Embedding dimension",
    ):
        service.retrieve(
            db,
            tenant_id=uuid4(),
            query="knowledge",
        )


def test_retrieve_ignores_chunks_without_embeddings():
    db = MagicMock()
    repository = MagicMock()
    embedding_service = MagicMock()

    tenant_id = uuid4()

    chunk = create_chunk(
        tenant_id=tenant_id,
        content="No embedding",
        chunk_index=0,
        embedding=None,
    )

    repository.list_ready_chunks_by_tenant.return_value = [
        chunk,
    ]

    embedding_service.dimensions = 2
    embedding_service.embed.return_value = [
        1.0,
        0.0,
    ]

    service = RetrievalService(
        document_chunk_repository=repository,
        embedding_service=embedding_service,
    )

    results = service.retrieve(
        db,
        tenant_id=tenant_id,
        query="knowledge",
    )

    assert results == []