import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.conversation import ConversationMessage
from app.models.enums import MessageRole


class ConversationMessageRepository:
    def get_next_message_index(
        self,
        db: Session,
        conversation_id: uuid.UUID,
    ) -> int:
        statement = select(
            func.coalesce(
                func.max(
                    ConversationMessage.message_index,
                ),
                -1,
            )
        ).where(
            ConversationMessage.conversation_id
            == conversation_id,
        )

        current_max = db.scalar(statement)

        return int(current_max) + 1

    def create(
        self,
        db: Session,
        *,
        conversation_id: uuid.UUID,
        message_index: int,
        role: MessageRole,
        content: str,
        sources: list | None = None,
    ) -> ConversationMessage:
        message = ConversationMessage(
            conversation_id=conversation_id,
            message_index=message_index,
            role=role,
            content=content,
            sources=sources,
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    def list_by_conversation(
        self,
        db: Session,
        conversation_id: uuid.UUID,
    ) -> list[ConversationMessage]:
        statement = (
            select(ConversationMessage)
            .where(
                ConversationMessage.conversation_id
                == conversation_id,
            )
            .order_by(
                ConversationMessage.message_index.asc(),
            )
        )

        return list(db.scalars(statement).all())