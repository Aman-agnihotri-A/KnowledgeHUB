import pytest

from app.rag.answer_generation import (
    AnswerGenerationRequest,
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