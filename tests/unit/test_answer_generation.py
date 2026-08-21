import pytest

from app.rag.answer_generation import (
    AnswerGenerationRequest,
    ConversationHistoryMessage,
    DeterministicAnswerGenerationProvider,
)


def test_deterministic_provider_generates_grounded_answer():
    provider = (
        DeterministicAnswerGenerationProvider()
    )

    result = provider.generate(
        AnswerGenerationRequest(
            question="What is KnowledgeHub?",
            context=(
                "[Source: handbook.pdf, chunk 0]\n"
                "KnowledgeHub is a knowledge platform."
            ),
        )
    )

    assert result.answer == (
        "Based on the available knowledge base:\n\n"
        "[Source: handbook.pdf, chunk 0]\n"
        "KnowledgeHub is a knowledge platform."
    )


def test_deterministic_provider_rejects_empty_question():
    provider = (
        DeterministicAnswerGenerationProvider()
    )

    with pytest.raises(
        ValueError,
        match="Question cannot be empty",
    ):
        provider.generate(
            AnswerGenerationRequest(
                question="   ",
                context="Some context",
            )
        )


def test_deterministic_provider_rejects_empty_context():
    provider = (
        DeterministicAnswerGenerationProvider()
    )

    with pytest.raises(
        ValueError,
        match="Grounding context cannot be empty",
    ):
        provider.generate(
            AnswerGenerationRequest(
                question="KnowledgeHub?",
                context="   ",
            )
        )


def test_provider_model_name_is_stable():
    provider = (
        DeterministicAnswerGenerationProvider()
    )

    assert provider.model_name == (
        "deterministic-grounded-v1"
    )

def test_generation_request_supports_conversation_history():
    history = [
        ConversationHistoryMessage(
            role="USER",
            content="What is KnowledgeHub?",
        ),
        ConversationHistoryMessage(
            role="ASSISTANT",
            content="KnowledgeHub is a knowledge platform.",
        ),
    ]

    request = AnswerGenerationRequest(
        question="What framework does it use?",
        context=(
            "[Source: handbook.pdf, chunk 0]\n"
            "KnowledgeHub uses FastAPI."
        ),
        conversation_history=history,
    )

    assert request.conversation_history == history

def test_deterministic_provider_ignores_history_for_now():
    provider = (
        DeterministicAnswerGenerationProvider()
    )

    result = provider.generate(
        AnswerGenerationRequest(
            question="What framework does it use?",
            context=(
                "[Source: handbook.pdf, chunk 0]\n"
                "KnowledgeHub uses FastAPI."
            ),
            conversation_history=[
                ConversationHistoryMessage(
                    role="USER",
                    content="What is KnowledgeHub?",
                ),
            ],
        )
    )

    assert result.answer == (
        "Based on the available knowledge base:\n\n"
        "[Source: handbook.pdf, chunk 0]\n"
        "KnowledgeHub uses FastAPI."
    )