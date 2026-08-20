import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole

class UserStatusUpdate(BaseModel):
    is_active: bool

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    tenant_id: uuid.UUID | None
    is_active: bool