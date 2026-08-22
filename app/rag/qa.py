import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.conversation import (
    ConversationMessage,
)
from app.core.config import settings
from app.rag.answer_generation import (
    AnswerGenerationError,
    AnswerGenerationProvider,
    AnswerGenerationRequest,
    ConversationHistoryMessage,
    create_answer_generation_provider,
)
from app.services.conversation import ConversationService
from app.services.retrieval import (
    RetrievedChunk,
    RetrievalService,
)


DEFAULT_CONVERSATION_HISTORY_LIMIT = 10


@dataclass(frozen=True)
class RAGSource:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_filename: str
    chunk_index: int
    similarity: float


@dataclass(frozen=True)
class RAGAnswer:
    question: str
    answer: str | None
    abstained: bool
    sources: list[RAGSource]
    conversation_id: uuid.UUID | None


class RAGQuestionAnsweringService:
    """
    Grounded RAG question-answering orchestration.

    Retrieval remains tenant-safe because it delegates to
    RetrievalService, which already scopes candidates by
    tenant and READY document state.

    When a conversation_id is supplied, the question and
    resulting answer/abstention are persisted through the
    existing ConversationService.

    Previous conversation messages are supplied to the
    answer-generation provider as conversational context.
    """

    def __init__(
        self,
        retrieval_service: RetrievalService | None = None,
        answer_provider: (
            AnswerGenerationProvider | None
        ) = None,
        conversation_service: (
            ConversationService | None
        ) = None,
        minimum_similarity: float = 0.0,
        conversation_history_limit: int = (
            DEFAULT_CONVERSATION_HISTORY_LIMIT
        ),
    ) -> None:
        if not 0.0 <= minimum_similarity <= 1.0:
            raise ValueError(
                "minimum_similarity must be between 0 and 1."
            )

        if conversation_history_limit < 1:
            raise ValueError(
                "conversation_history_limit must be "
                "greater than zero."
            )

        self.retrieval_service = (
            retrieval_service
            or RetrievalService()
        )

        self.answer_provider = (
            answer_provider
            or create_answer_generation_provider(
                provider_name=(
                    settings.answer_generation_provider
                ),
                openai_api_key=settings.openai_api_key,
                openai_model=settings.openai_model,
                gemini_api_key=settings.gemini_api_key,
                gemini_model=settings.gemini_model,
            )
        )

        self.conversation_service = (
            conversation_service
            or ConversationService()
        )

        self.minimum_similarity = (
            minimum_similarity
        )

        self.conversation_history_limit = (
            conversation_history_limit
        )

    def ask(
        self,
        db: Session,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        question: str,
        top_k: int = 5,
        conversation_id: uuid.UUID | None = None,
    ) -> RAGAnswer:
        normalized_question = question.strip()

        if not normalized_question:
            raise ValueError(
                "Question cannot be empty."
            )

        if (
            conversation_id is not None
            and user_id is None
        ):
            raise ValueError(
                "user_id is required when conversation_id is provided."
            )

        conversation_history: list[
            ConversationHistoryMessage
        ] = []

        if conversation_id is not None:
            conversation = (
                self.conversation_service.get_conversation(
                    db,
                    conversation_id=conversation_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                )
            )

            if conversation is None:
                raise ValueError(
                    "Conversation not found."
                )

            previous_messages = (
                self.conversation_service
                .list_recent_messages(
                    db,
                    conversation_id=conversation_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    limit=self.conversation_history_limit,
                )
            )

            conversation_history = [
                ConversationHistoryMessage(
                    role=message.role.value,
                    content=message.content,
                )
                for message in previous_messages
            ]

        retrieved = self.retrieval_service.retrieve(
            db,
            tenant_id=tenant_id,
            query=normalized_question,
            top_k=top_k,
        )

        eligible = [
            result
            for result in retrieved
            if result.similarity
            >= self.minimum_similarity
        ]

        sources = [
            self._build_source(result)
            for result in eligible
        ]

        if conversation_id is not None:
            self.conversation_service.append_user_message(
                db,
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                user_id=user_id,
                content=normalized_question,
            )

        if not eligible:
            if conversation_id is not None:
                self.conversation_service.append_assistant_message(
                    db,
                    conversation_id=conversation_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    content=(
                        "I could not find relevant information "
                        "in the available knowledge base."
                    ),
                    sources=[],
                )

            return RAGAnswer(
                question=normalized_question,
                answer=None,
                abstained=True,
                sources=[],
                conversation_id=conversation_id,
            )

        context = self._build_context(
            eligible,
        )

        try:
            generated = self.answer_provider.generate(
                AnswerGenerationRequest(
                    question=normalized_question,
                    context=context,
                    conversation_history=conversation_history,
                )
            )
        except AnswerGenerationError:
            raise
        except Exception as exc:
            raise AnswerGenerationError(
                "Answer Generation Failed."
            ) from exc

        if conversation_id is not None:
            persisted_sources = [
                self._source_to_metadata(source)
                for source in sources
            ]

            self.conversation_service.append_assistant_message(
                db,
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                user_id=user_id,
                content=generated.answer,
                sources=persisted_sources,
            )

        return RAGAnswer(
            question=normalized_question,
            answer=generated.answer,
            abstained=False,
            sources=sources,
            conversation_id=conversation_id,
        )

    @staticmethod
    def _build_context(
        results: list[RetrievedChunk],
    ) -> str:
        sections: list[str] = []

        for result in results:
            chunk = result.chunk

            sections.append(
                (
                    f"[Source: {chunk.document.filename}, "
                    f"chunk {chunk.chunk_index}]\n"
                    f"{chunk.content}"
                )
            )

        return "\n\n".join(sections)

    @staticmethod
    def _build_source(
        result: RetrievedChunk,
    ) -> RAGSource:
        chunk = result.chunk

        return RAGSource(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            document_filename=(
                chunk.document.filename
            ),
            chunk_index=chunk.chunk_index,
            similarity=result.similarity,
        )

    @staticmethod
    def _source_to_metadata(
        source: RAGSource,
    ) -> dict:
        return {
            "chunk_id": str(source.chunk_id),
            "document_id": str(source.document_id),
            "document_filename": (
                source.document_filename
            ),
            "chunk_index": source.chunk_index,
            "similarity": source.similarity,
        }