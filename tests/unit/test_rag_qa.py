from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.enums import DocumentStatus
from app.rag.answer_generation import (
    AnswerGenerationResponse,
)
from app.rag.qa import (
    RAGQuestionAnsweringService,
)
from app.services.retrieval import RetrievedChunk


def create_retrieved_chunk(
    *,
    tenant_id,
    content,
    chunk_index,
    similarity,
):
    document = Document(
        tenant_id=tenant_id,
        uploaded_by=uuid4(),
        filename="handbook.pdf",
        storage_path="documents/handbook.pdf",
        status=DocumentStatus.READY,
    )

    document.id = uuid4()

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=chunk_index,
        content=content,
    )

    chunk.id = uuid4()
    chunk.document = document

    return RetrievedChunk(
        chunk=chunk,
        similarity=similarity,
    )


def test_ask_generates_grounded_answer():
    db = MagicMock()
    retrieval_service = MagicMock()
    answer_provider = MagicMock()

    tenant_id = uuid4()

    retrieved = create_retrieved_chunk(
        tenant_id=tenant_id,
        content="KnowledgeHub uses FastAPI.",
        chunk_index=0,
        similarity=0.95,
    )

    retrieval_service.retrieve.return_value = [
        retrieved,
    ]

    answer_provider.generate.return_value = (
        AnswerGenerationResponse(
            answer="KnowledgeHub uses FastAPI."
        )
    )

    service = RAGQuestionAnsweringService(
        retrieval_service=retrieval_service,
        answer_provider=answer_provider,
        minimum_similarity=0.7,
    )

    result = service.ask(
        db,
        tenant_id=tenant_id,
        question="What framework does KnowledgeHub use?",
        top_k=3,
    )

    assert result.question == (
        "What framework does KnowledgeHub use?"
    )
    assert result.answer == (
        "KnowledgeHub uses FastAPI."
    )
    assert result.abstained is False
    assert len(result.sources) == 1

    assert (
        result.sources[0].document_filename
        == "handbook.pdf"
    )

    retrieval_service.retrieve.assert_called_once_with(
        db,
        tenant_id=tenant_id,
        query=(
            "What framework does KnowledgeHub use?"
        ),
        top_k=3,
    )

    answer_provider.generate.assert_called_once()


def test_ask_abstains_when_no_chunks_are_retrieved():
    db = MagicMock()
    retrieval_service = MagicMock()
    answer_provider = MagicMock()

    retrieval_service.retrieve.return_value = []

    service = RAGQuestionAnsweringService(
        retrieval_service=retrieval_service,
        answer_provider=answer_provider,
        minimum_similarity=0.7,
    )

    result = service.ask(
        db,
        tenant_id=uuid4(),
        question="Unknown question",
    )

    assert result.answer is None
    assert result.abstained is True
    assert result.sources == []

    answer_provider.generate.assert_not_called()


def test_ask_abstains_when_results_are_below_threshold():
    db = MagicMock()
    retrieval_service = MagicMock()
    answer_provider = MagicMock()

    tenant_id = uuid4()

    retrieved = create_retrieved_chunk(
        tenant_id=tenant_id,
        content="Weakly related content.",
        chunk_index=0,
        similarity=0.42,
    )

    retrieval_service.retrieve.return_value = [
        retrieved,
    ]

    service = RAGQuestionAnsweringService(
        retrieval_service=retrieval_service,
        answer_provider=answer_provider,
        minimum_similarity=0.7,
    )

    result = service.ask(
        db,
        tenant_id=tenant_id,
        question="Unrelated question",
    )

    assert result.answer is None
    assert result.abstained is True
    assert result.sources == []

    answer_provider.generate.assert_not_called()


def test_ask_passes_only_eligible_results_to_generator():
    db = MagicMock()
    retrieval_service = MagicMock()
    answer_provider = MagicMock()

    tenant_id = uuid4()

    strong = create_retrieved_chunk(
        tenant_id=tenant_id,
        content="Strong context.",
        chunk_index=0,
        similarity=0.91,
    )

    weak = create_retrieved_chunk(
        tenant_id=tenant_id,
        content="Weak context.",
        chunk_index=1,
        similarity=0.31,
    )

    retrieval_service.retrieve.return_value = [
        strong,
        weak,
    ]

    answer_provider.generate.return_value = (
        AnswerGenerationResponse(
            answer="Grounded answer."
        )
    )

    service = RAGQuestionAnsweringService(
        retrieval_service=retrieval_service,
        answer_provider=answer_provider,
        minimum_similarity=0.7,
    )

    result = service.ask(
        db,
        tenant_id=tenant_id,
        question="Question",
    )

    assert result.abstained is False
    assert len(result.sources) == 1
    assert result.sources[0].chunk_id == (
        strong.chunk.id
    )

    request = (
        answer_provider.generate.call_args.args[0]
    )

    assert "Strong context." in request.context
    assert "Weak context." not in request.context


def test_ask_rejects_empty_question():
    db = MagicMock()

    service = RAGQuestionAnsweringService(
        retrieval_service=MagicMock(),
        answer_provider=MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="Question cannot be empty",
    ):
        service.ask(
            db,
            tenant_id=uuid4(),
            question="   ",
        )


def test_invalid_similarity_threshold_is_rejected():
    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):
        RAGQuestionAnsweringService(
            minimum_similarity=1.5,
        )


def test_context_contains_source_metadata():
    db = MagicMock()
    retrieval_service = MagicMock()
    answer_provider = MagicMock()

    tenant_id = uuid4()

    retrieved = create_retrieved_chunk(
        tenant_id=tenant_id,
        content="Important policy information.",
        chunk_index=3,
        similarity=0.9,
    )

    retrieval_service.retrieve.return_value = [
        retrieved,
    ]

    answer_provider.generate.return_value = (
        AnswerGenerationResponse(
            answer="Policy answer.",
        )
    )

    service = RAGQuestionAnsweringService(
        retrieval_service=retrieval_service,
        answer_provider=answer_provider,
    )

    service.ask(
        db,
        tenant_id=tenant_id,
        question="What is the policy?",
    )

    request = (
        answer_provider.generate.call_args.args[0]
    )

    assert (
        "[Source: handbook.pdf, chunk 3]"
        in request.context
    )

    assert (
        "Important policy information."
        in request.context
    )