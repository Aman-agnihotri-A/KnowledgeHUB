import uuid

from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user import UserRepository


class UserService:
    def __init__(
        self,
        repository: UserRepository | None = None,
    ) -> None:
        self.repository = repository or UserRepository()

    def create_user(
        self,
        db: Session,
        *,
        email: str,
        hashed_password: str,
        full_name: str,
        role: UserRole,
        tenant_id: uuid.UUID | None = None,
    ) -> User:
        existing_user = self.repository.get_by_email(
            db,
            email,
        )

        if existing_user is not None:
            raise ValueError(
                f"User with email '{email}' already exists."
            )

        if role == UserRole.SUPER_ADMIN:
            if tenant_id is not None:
                raise ValueError(
                    "Super Admin cannot belong to a tenant."
                )
        elif tenant_id is None:
            raise ValueError(
                f"{role.value} must belong to a tenant."
            )

        return self.repository.create(
            db,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            tenant_id=tenant_id,
        )

    def get_user(
        self,
        db: Session,
        user_id: uuid.UUID,
    ) -> User | None:
        return self.repository.get_by_id(
            db,
            user_id,
        )

    def get_user_by_email(
        self,
        db: Session,
        email: str,
    ) -> User | None:
        return self.repository.get_by_email(
            db,
            email,
        )

    def list_tenant_users(
        self,
        db: Session,
        tenant_id: uuid.UUID,
    ) -> list[User]:
        return self.repository.list_by_tenant(
            db,
            tenant_id,
        )

    def list_active_tenant_users(
        self,
        db: Session,
        tenant_id: uuid.UUID,
    ) -> list[User]:
        return self.repository.list_active_by_tenant(
            db,
            tenant_id,
        )