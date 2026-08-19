import uuid

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    filename: str
    storage_path: str


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    uploaded_by: uuid.UUID
    filename: str
    storage_path: str
    status: str