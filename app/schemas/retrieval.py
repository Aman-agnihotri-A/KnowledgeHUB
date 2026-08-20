import uuid

from pydantic import BaseModel, ConfigDict, Field


class RetrievalResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_filename: str
    chunk_index: int
    content: str
    similarity: float


class RetrievalResponse(BaseModel):
    results: list[RetrievalResult]