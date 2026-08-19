import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User


class UserRepository:
    def create(
        self,
        db: Session,
        *,
        email: str,
        hashed_password: str,
        full_name: str,
        role: UserRole,
        tenant_id: uuid.UUID | None = None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            tenant_id=tenant_id,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def get_by_id(
        self,
        db: Session,
        user_id: uuid.UUID,
    ) -> User | None:
        statement = select(User).where(
            User.id == user_id
        )

        return db.scalar(statement)

    def get_by_email(
        self,
        db: Session,
        email: str,
    ) -> User | None:
        statement = select(User).where(
            User.email == email
        )

        return db.scalar(statement)

    def list_by_tenant(
        self,
        db: Session,
        tenant_id: uuid.UUID,
    ) -> list[User]:
        statement = (
            select(User)
            .where(User.tenant_id == tenant_id)
            .order_by(User.email)
        )

        return list(db.scalars(statement).all())

    def list_active_by_tenant(
        self,
        db: Session,
        tenant_id: uuid.UUID,
    ) -> list[User]:
        statement = (
            select(User)
            .where(
                User.tenant_id == tenant_id,
                User.is_active.is_(True),
            )
            .order_by(User.email)
        )

        return list(db.scalars(statement).all())