from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.enums import DocumentStatus, MessageRole
from app.models.conversation import Conversation
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

def test_ask_persists_question_and_answer_in_conversation():
    db = MagicMock()

    tenant_id = uuid4()
    user_id = uuid4()
    conversation_id = uuid4()

    retrieval_service = MagicMock()
    conversation_service = MagicMock()
    answer_provider = MagicMock()

    conversation_service.get_conversation.return_value = (
        Conversation(
            id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title="Knowledge",
        )
    )

    answer = MagicMock()
    answer.answer = (
        "KnowledgeHub is a knowledge platform."
    )

    answer_provider.generate.return_value = answer

    service = RAGQuestionAnsweringService(
        retrieval_service=retrieval_service,
        answer_provider=answer_provider,
        conversation_service=conversation_service,
    )

    retrieval_service.retrieve.return_value = []

    result = service.ask(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
        question="  What is KnowledgeHub?  ",
    )

    assert result.question == (
        "What is KnowledgeHub?"
    )
    assert result.answer is None
    assert result.abstained is True

    conversation_service.get_conversation.assert_called_once_with(
        db,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    conversation_service.append_user_message.assert_called_once_with(
        db,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=user_id,
        content="What is KnowledgeHub?",
    )

    conversation_service.append_assistant_message.assert_called_once()


def test_ask_rejects_inaccessible_conversation():
    db = MagicMock()

    conversation_service = MagicMock()

    conversation_service.get_conversation.return_value = None

    service = RAGQuestionAnsweringService(
        retrieval_service=MagicMock(),
        answer_provider=MagicMock(),
        conversation_service=conversation_service,
    )

    with pytest.raises(
        ValueError,
        match="Conversation not found",
    ):
        service.ask(
            db,
            tenant_id=uuid4(),
            user_id=uuid4(),
            conversation_id=uuid4(),
            question="What is KnowledgeHub?",
        )


def test_ask_requires_user_id_for_conversation():
    db = MagicMock()

    service = RAGQuestionAnsweringService(
        retrieval_service=MagicMock(),
        answer_provider=MagicMock(),
        conversation_service=MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="user_id is required",
    ):
        service.ask(
            db,
            tenant_id=uuid4(),
            user_id=None,
            conversation_id=uuid4(),
            question="What is KnowledgeHub?",
        )


def test_ask_without_conversation_remains_backward_compatible():
    db = MagicMock()

    retrieval_service = MagicMock()
    conversation_service = MagicMock()

    service = RAGQuestionAnsweringService(
        retrieval_service=retrieval_service,
        answer_provider=MagicMock(),
        conversation_service=conversation_service,
    )

    retrieval_service.retrieve.return_value = []

    result = service.ask(
        db,
        tenant_id=uuid4(),
        question="What is KnowledgeHub?",
    )

    assert result.conversation_id is None

    conversation_service.get_conversation.assert_not_called()
    conversation_service.append_user_message.assert_not_called()
    conversation_service.append_assistant_message.assert_not_called()

def test_ask_persists_grounded_answer_and_sources():
    db = MagicMock()

    tenant_id = uuid4()
    user_id = uuid4()
    conversation_id = uuid4()

    retrieval_service = MagicMock()
    conversation_service = MagicMock()
    answer_provider = MagicMock()

    conversation_service.get_conversation.return_value = (
        Conversation(
            id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title="Knowledge",
        )
    )

    chunk = MagicMock()
    chunk.id = uuid4()
    chunk.document_id = uuid4()
    chunk.document.filename = "handbook.pdf"
    chunk.chunk_index = 3
    chunk.content = "KnowledgeHub is a knowledge platform."

    retrieved = MagicMock()
    retrieved.chunk = chunk
    retrieved.similarity = 0.95

    retrieval_service.retrieve.return_value = [
        retrieved,
    ]

    generated = MagicMock()
    generated.answer = (
        "KnowledgeHub is a knowledge platform."
    )

    answer_provider.generate.return_value = generated

    service = RAGQuestionAnsweringService(
        retrieval_service=retrieval_service,
        answer_provider=answer_provider,
        conversation_service=conversation_service,
    )

    result = service.ask(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
        question="What is KnowledgeHub?",
    )

    assert result.answer == (
        "KnowledgeHub is a knowledge platform."
    )
    assert result.abstained is False
    assert result.conversation_id == conversation_id

    conversation_service.append_user_message.assert_called_once_with(
        db,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=user_id,
        content="What is KnowledgeHub?",
    )

    conversation_service.append_assistant_message.assert_called_once_with(
        db,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=user_id,
        content="KnowledgeHub is a knowledge platform.",
        sources=[
            {
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "document_filename": "handbook.pdf",
                "chunk_index": 3,
                "similarity": 0.95,
            }
        ],
    )

def test_ask_passes_previous_conversation_history_to_generator():
    db = MagicMock()

    tenant_id = uuid4()
    user_id = uuid4()
    conversation_id = uuid4()

    retrieval_service = MagicMock()
    conversation_service = MagicMock()
    answer_provider = MagicMock()

    conversation_service.get_conversation.return_value = (
        Conversation(
            id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title="Knowledge conversation",
        )
    )

    conversation_service.list_recent_messages.return_value = [
        MagicMock(
            role=MessageRole.USER,
            content="What is KnowledgeHub?",
        ),
        MagicMock(
            role=MessageRole.ASSISTANT,
            content="It is a knowledge platform.",
        ),
    ]

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
            answer="It uses FastAPI."
        )
    )

    service = RAGQuestionAnsweringService(
        retrieval_service=retrieval_service,
        answer_provider=answer_provider,
        conversation_service=conversation_service,
    )

    result = service.ask(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
        question="What framework does it use?",
    )

    assert result.answer == "It uses FastAPI."

    conversation_service.list_recent_messages.assert_called_once_with(
        db,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=user_id,
        limit=10,
    )

    request = (
        answer_provider.generate.call_args.args[0]
    )

    assert len(request.conversation_history) == 2

    assert request.conversation_history[0].role == "user"
    assert (
        request.conversation_history[0].content
        == "What is KnowledgeHub?"
    )

    assert (
        request.conversation_history[1].role
        == "assistant"
    )

    assert (
        request.conversation_history[1].content
        == "It is a knowledge platform."
    )

    assert request.question == (
        "What framework does it use?"
    )

    assert "KnowledgeHub uses FastAPI." in (
        request.context
    )

def test_ask_without_conversation_does_not_load_history():
    db = MagicMock()

    retrieval_service = MagicMock()
    conversation_service = MagicMock()
    answer_provider = MagicMock()

    retrieved = create_retrieved_chunk(
        tenant_id=uuid4(),
        content="KnowledgeHub uses FastAPI.",
        chunk_index=0,
        similarity=0.95,
    )

    retrieval_service.retrieve.return_value = [
        retrieved,
    ]

    answer_provider.generate.return_value = (
        AnswerGenerationResponse(
            answer="It uses FastAPI."
        )
    )

    service = RAGQuestionAnsweringService(
        retrieval_service=retrieval_service,
        answer_provider=answer_provider,
        conversation_service=conversation_service,
    )

    service.ask(
        db,
        tenant_id=uuid4(),
        question="What framework does it use?",
    )

    conversation_service.get_conversation.assert_not_called()
    conversation_service.list_recent_messages.assert_not_called()

    request = (
        answer_provider.generate.call_args.args[0]
    )

    assert request.conversation_history == []

def test_invalid_conversation_history_limit_is_rejected():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        RAGQuestionAnsweringService(
            conversation_history_limit=0,
        )