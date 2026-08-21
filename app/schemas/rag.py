import uuid

from pydantic import BaseModel, Field


class RAGAskRequest(BaseModel):
    question: str = Field(
        min_length=1,
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
    )
    conversation_id: uuid.UUID | None = None


class RAGSourceRead(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_filename: str
    chunk_index: int
    similarity: float


class RAGAskResponse(BaseModel):
    question: str
    answer: str | None
    abstained: bool
    sources: list[RAGSourceRead]
    conversation_id: uuid.UUID | None = None