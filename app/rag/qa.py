import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.rag.answer_generation import (
    AnswerGenerationProvider,
    AnswerGenerationRequest,
    DeterministicAnswerGenerationProvider,
)
from app.services.retrieval import (
    RetrievedChunk,
    RetrievalService,
)


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


class RAGQuestionAnsweringService:
    """
    Grounded RAG question-answering orchestration.

    Retrieval remains tenant-safe because it delegates to
    RetrievalService, which already scopes candidates by
    tenant and READY document state.
    """

    def __init__(
        self,
        retrieval_service: RetrievalService | None = None,
        answer_provider: (
            AnswerGenerationProvider | None
        ) = None,
        minimum_similarity: float = 0.0,
    ) -> None:
        if not 0.0 <= minimum_similarity <= 1.0:
            raise ValueError(
                "minimum_similarity must be between 0 and 1."
            )

        self.retrieval_service = (
            retrieval_service
            or RetrievalService()
        )

        self.answer_provider = (
            answer_provider
            or DeterministicAnswerGenerationProvider()
        )

        self.minimum_similarity = (
            minimum_similarity
        )

    def ask(
        self,
        db: Session,
        *,
        tenant_id: uuid.UUID,
        question: str,
        top_k: int = 5,
    ) -> RAGAnswer:
        normalized_question = question.strip()

        if not normalized_question:
            raise ValueError(
                "Question cannot be empty."
            )

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

        if not eligible:
            return RAGAnswer(
                question=normalized_question,
                answer=None,
                abstained=True,
                sources=[],
            )

        context = self._build_context(
            eligible,
        )

        generated = self.answer_provider.generate(
            AnswerGenerationRequest(
                question=normalized_question,
                context=context,
            )
        )

        return RAGAnswer(
            question=normalized_question,
            answer=generated.answer,
            abstained=False,
            sources=sources,
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