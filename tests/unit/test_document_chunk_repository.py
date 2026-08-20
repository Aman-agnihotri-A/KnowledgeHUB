from unittest.mock import MagicMock
from uuid import uuid4

from app.models.document_chunk import DocumentChunk
from app.repositories.document_chunk import (
    DocumentChunkRepository,
)


def test_create_and_list_chunks():
    db = MagicMock()
    repository = DocumentChunkRepository()

    document_id = uuid4()

    chunks = repository.create_many(
        db,
        document_id=document_id,
        chunks=[
            "First chunk",
            "Second chunk",
            "Third chunk",
        ],
    )

    assert len(chunks) == 3

    assert all(
        isinstance(
            chunk,
            DocumentChunk,
        )
        for chunk in chunks
    )

    assert [
        chunk.chunk_index
        for chunk in chunks
    ] == [0, 1, 2]

    assert [
        chunk.content
        for chunk in chunks
    ] == [
        "First chunk",
        "Second chunk",
        "Third chunk",
    ]

    assert all(
        chunk.document_id == document_id
        for chunk in chunks
    )

    db.add_all.assert_called_once_with(
        chunks
    )

    db.flush.assert_called_once()


def test_create_many_with_empty_chunks():
    db = MagicMock()
    repository = DocumentChunkRepository()

    document_id = uuid4()

    result = repository.create_many(
        db,
        document_id=document_id,
        chunks=[],
    )

    assert result == []

    db.add_all.assert_not_called()
    db.flush.assert_called_once()


def test_delete_by_document():
    db = MagicMock()
    repository = DocumentChunkRepository()

    document_id = uuid4()

    repository.delete_by_document(
        db,
        document_id,
    )

    db.execute.assert_called_once()


def test_list_by_document():
    db = MagicMock()
    repository = DocumentChunkRepository()

    document_id = uuid4()

    chunks = [
        DocumentChunk(
            document_id=document_id,
            chunk_index=0,
            content="First chunk",
        ),
        DocumentChunk(
            document_id=document_id,
            chunk_index=1,
            content="Second chunk",
        ),
    ]

    db.scalars.return_value.all.return_value = (
        chunks
    )

    result = repository.list_by_document(
        db,
        document_id,
    )

    assert result == chunks

    db.scalars.assert_called_once()

def test_create_many_assigns_sequential_indexes():
    db = MagicMock()
    repository = DocumentChunkRepository()

    document_id = uuid4()

    chunks = repository.create_many(
        db,
        document_id=document_id,
        chunks=[
            "Chunk A",
            "Chunk B",
            "Chunk C",
            "Chunk D",
        ],
    )

    assert [
        chunk.chunk_index
        for chunk in chunks
    ] == [0, 1, 2, 3]

    assert [
        chunk.document_id
        for chunk in chunks
    ] == [
        document_id,
        document_id,
        document_id,
        document_id,
    ]

    db.add_all.assert_called_once_with(
        chunks
    )

    db.flush.assert_called_once()

def test_update_embeddings():
    db = MagicMock()

    repository = DocumentChunkRepository()

    first_id = uuid4()
    second_id = uuid4()

    first = DocumentChunk(
        document_id=uuid4(),
        chunk_index=0,
        content="First",
    )

    first.id = first_id

    second = DocumentChunk(
        document_id=first.document_id,
        chunk_index=1,
        content="Second",
    )

    second.id = second_id

    db.scalars.return_value.all.return_value = [
        first,
        second,
    ]

    embeddings = {
        first_id: [
            0.1,
            0.2,
        ],
        second_id: [
            0.3,
            0.4,
        ],
    }

    repository.update_embeddings(
        db,
        embeddings,
    )

    assert first.embedding == [
        0.1,
        0.2,
    ]

    assert second.embedding == [
        0.3,
        0.4,
    ]

    db.flush.assert_called_once()


def test_update_embeddings_with_empty_mapping():
    db = MagicMock()

    repository = DocumentChunkRepository()

    repository.update_embeddings(
        db,
        {},
    )

    db.scalars.assert_not_called()
    db.flush.assert_not_called()