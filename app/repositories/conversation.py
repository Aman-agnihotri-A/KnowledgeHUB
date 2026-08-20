import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation


class ConversationRepository:
    def create(
        self,
        db: Session,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None,
    ) -> Conversation:
        conversation = Conversation(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return conversation

    def get_by_id(
        self,
        db: Session,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
        )

        return db.scalar(statement)

    def list_by_user(
        self,
        db: Session,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[Conversation]:
        statement = (
            select(Conversation)
            .where(
                Conversation.tenant_id == tenant_id,
                Conversation.user_id == user_id,
            )
            .order_by(
                Conversation.created_at.desc(),
            )
        )

        return list(db.scalars(statement).all())