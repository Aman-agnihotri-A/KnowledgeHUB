import pytest

from app.services.embedding import (
    DeterministicEmbeddingService,
)


def test_embedding_has_configured_dimensions():
    service = DeterministicEmbeddingService(
        dimensions=8,
    )

    embedding = service.embed(
        "KnowledgeHub"
    )

    assert len(embedding) == 8


def test_embedding_is_deterministic():
    service = DeterministicEmbeddingService(
        dimensions=8,
    )

    first = service.embed(
        "KnowledgeHub"
    )

    second = service.embed(
        "KnowledgeHub"
    )

    assert first == second


def test_different_text_can_produce_different_embedding():
    service = DeterministicEmbeddingService(
        dimensions=8,
    )

    first = service.embed(
        "KnowledgeHub"
    )

    second = service.embed(
        "PostgreSQL"
    )

    assert first != second


def test_embedding_is_normalized():
    service = DeterministicEmbeddingService(
        dimensions=8,
    )

    embedding = service.embed(
        "KnowledgeHub"
    )

    magnitude = sum(
        value * value
        for value in embedding
    ) ** 0.5

    assert magnitude == pytest.approx(
        1.0,
    )


def test_empty_text_is_rejected():
    service = DeterministicEmbeddingService()

    with pytest.raises(
        ValueError,
        match="empty text",
    ):
        service.embed("   ")


def test_invalid_dimensions_are_rejected():
    with pytest.raises(
        ValueError,
        match="dimensions",
    ):
        DeterministicEmbeddingService(
            dimensions=0,
        )