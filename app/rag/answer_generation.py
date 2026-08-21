from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ConversationHistoryMessage:
    role: str
    content: str


@dataclass(frozen=True)
class AnswerGenerationRequest:
    question: str
    context: str
    conversation_history: list[
        ConversationHistoryMessage
    ] | None = None


@dataclass(frozen=True)
class AnswerGenerationResponse:
    answer: str


class AnswerGenerationProvider(ABC):
    """Interface for grounded answer generation."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        request: AnswerGenerationRequest,
    ) -> AnswerGenerationResponse:
        raise NotImplementedError


class DeterministicAnswerGenerationProvider(
    AnswerGenerationProvider,
):
    """
    Local deterministic answer provider.

    This provider intentionally does not call an external
    LLM. It provides predictable grounded behavior for
    local development and automated tests.

    A production LLM provider can implement the same
    AnswerGenerationProvider interface later.
    """

    @property
    def model_name(self) -> str:
        return "deterministic-grounded-v1"

    def generate(
        self,
        request: AnswerGenerationRequest,
    ) -> AnswerGenerationResponse:
        question = request.question.strip()
        context = request.context.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        if not context:
            raise ValueError(
                "Grounding context cannot be empty."
            )

        return AnswerGenerationResponse(
            answer=(
                "Based on the available knowledge base:\n\n"
                f"{context}"
            )
        )