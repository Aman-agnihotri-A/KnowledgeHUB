import uuid

from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user import UserRepository
from app.core.security import hash_password,verify_password


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
        password: str,
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
            hashed_password=hash_password(password),
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
    def authenticate_user(
        self,
        db: Session,
        *,
        email: str,
        password: str,
    ) -> User | None:
        user = self.repository.get_by_email(
            db,
            email,
        )

        if user is None:
            return None

        if not user.is_active:
            return None

        if not verify_password(
            password,
            user.hashed_password,
        ):
            return None

        return user
    def update_user_status(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        is_active: bool,
    ) -> User:
        user = self.repository.get_by_id(
            db,
            user_id,
        )

        if user is None:
            raise ValueError("User not found.")

        if user.role == UserRole.SUPER_ADMIN:
            raise ValueError(
                "Super Admin users cannot be managed through "
                "tenant user administration."
            )

        if user.tenant_id != tenant_id:
            raise ValueError(
                "User does not belong to the specified tenant."
            )

        return self.repository.update_active_status(
            db,
            user,
            is_active=is_active,
        )