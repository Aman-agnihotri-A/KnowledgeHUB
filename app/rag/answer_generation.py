from abc import ABC, abstractmethod
from dataclasses import dataclass

from openai import OpenAI


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


class AnswerGenerationError(Exception):
    """Raised when answer generation cannot complete."""


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


class OpenAIAnswerGenerationProvider(
    AnswerGenerationProvider,
):
    """
    Production answer-generation provider backed by
    the OpenAI Responses API.

    Retrieved document context is treated as the only
    factual grounding source.

    Conversation history is supplied only to resolve
    conversational references and continuity.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        client: OpenAI | None = None,
    ) -> None:
        normalized_api_key = api_key.strip()
        normalized_model = model.strip()

        if not normalized_api_key:
            raise ValueError(
                "OpenAI API key is required."
            )

        if not normalized_model:
            raise ValueError(
                "OpenAI model is required."
            )

        self._model = normalized_model

        self._client = client or OpenAI(
            api_key=normalized_api_key,
        )

    @property
    def model_name(self) -> str:
        return self._model

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

        prompt = self._build_prompt(request)

        try:
            response = (
                self._client.responses.create(
                    model=self._model,
                    input=prompt,
                )
            )
        except Exception as exc:
            raise AnswerGenerationError(
                "OpenAI answer generation failed."
            ) from exc

        answer = getattr(
            response,
            "output_text",
            None,
        )

        if not isinstance(answer, str):
            raise AnswerGenerationError(
                "OpenAI returned an invalid answer."
            )

        answer = answer.strip()

        if not answer:
            raise AnswerGenerationError(
                "OpenAI returned an empty answer."
            )

        return AnswerGenerationResponse(
            answer=answer,
        )

    @staticmethod
    def _build_prompt(
        request: AnswerGenerationRequest,
    ) -> str:
        history = (
            request.conversation_history
            or []
        )

        history_lines: list[str] = []

        for message in history:
            role = message.role.strip().lower()
            content = message.content.strip()

            if not role or not content:
                continue

            history_lines.append(
                f"{role}: {content}"
            )

        conversation_section = (
            "\n".join(history_lines)
            if history_lines
            else "(No previous conversation.)"
        )

        return (
            "You are the answer-generation component "
            "of KnowledgeHub, a multi-tenant knowledge "
            "assistance system.\n\n"
            "Answer the user's question using ONLY the "
            "retrieved knowledge-base context as the "
            "factual source.\n\n"
            "Conversation history may be used to resolve "
            "references such as 'it', 'they', or 'that', "
            "but previous assistant messages are not "
            "authoritative knowledge sources.\n\n"
            "If the retrieved context does not contain "
            "enough information to answer the question, "
            "say that the available knowledge base does "
            "not contain enough information. Do not "
            "invent facts.\n\n"
            "Be concise and directly answer the question.\n\n"
            "CONVERSATION HISTORY:\n"
            f"{conversation_section}\n\n"
            "RETRIEVED KNOWLEDGE:\n"
            f"{request.context.strip()}\n\n"
            "CURRENT QUESTION:\n"
            f"{request.question.strip()}"
        )


def create_answer_generation_provider(
    *,
    provider_name: str,
    openai_api_key: str | None,
    openai_model: str,
) -> AnswerGenerationProvider:
    normalized_provider = (
        provider_name.strip().lower()
    )

    if normalized_provider == "deterministic":
        return (
            DeterministicAnswerGenerationProvider()
        )

    if normalized_provider == "openai":
        if not openai_api_key:
            raise ValueError(
                "OpenAI API key is required when "
                "ANSWER_GENERATION_PROVIDER is 'openai'."
            )

        return OpenAIAnswerGenerationProvider(
            api_key=openai_api_key,
            model=openai_model,
        )

    raise ValueError(
        "Unsupported answer generation provider: "
        f"{provider_name}"
    )