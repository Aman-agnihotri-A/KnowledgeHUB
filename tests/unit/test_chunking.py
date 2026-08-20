import pytest

from app.services.chunking import (
    TextChunkingService,
)


def test_rejects_invalid_chunk_size():
    with pytest.raises(
        ValueError,
        match="chunk_size",
    ):
        TextChunkingService(
            chunk_size=0
        )


def test_rejects_invalid_overlap():
    with pytest.raises(
        ValueError,
        match="chunk_overlap",
    ):
        TextChunkingService(
            chunk_size=100,
            chunk_overlap=100,
        )


def test_empty_text_returns_no_chunks():
    service = TextChunkingService()

    assert service.split("") == []


def test_whitespace_only_text_returns_no_chunks():
    service = TextChunkingService()

    assert service.split("   \n\t ") == []


def test_text_is_split_into_multiple_chunks():
    service = TextChunkingService(
        chunk_size=20,
        chunk_overlap=5,
    )

    text = (
        "KnowledgeHub processes "
        "documents into chunks "
        "for future retrieval."
    )

    chunks = service.split(text)

    assert len(chunks) > 1
    assert all(chunks)

    assert chunks[0] == (
        "KnowledgeHub"
    )

    assert any(
        "documents" in chunk
        for chunk in chunks
    )

    assert any(
        "retrieval" in chunk
        for chunk in chunks
    )


def test_chunks_respect_maximum_size():
    service = TextChunkingService(
        chunk_size=20,
        chunk_overlap=5,
    )

    text = (
        "KnowledgeHub processes "
        "documents into chunks "
        "for future retrieval."
    )

    chunks = service.split(text)

    assert all(
        len(chunk) <= 20
        for chunk in chunks
    )


def test_short_text_remains_single_chunk():
    service = TextChunkingService(
        chunk_size=100,
        chunk_overlap=10,
    )

    text = "KnowledgeHub"

    assert service.split(text) == [
        text
    ]