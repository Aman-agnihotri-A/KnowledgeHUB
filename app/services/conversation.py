import uuid

from sqlalchemy.orm import Session

from app.models.conversation import (
    Conversation,
    ConversationMessage,
)
from app.models.enums import MessageRole
from app.repositories.conversation import (
    ConversationRepository,
)
from app.repositories.conversation_message import (
    ConversationMessageRepository,
)
from app.repositories.user import UserRepository


class ConversationService:
    def __init__(
        self,
        conversation_repository: (
            ConversationRepository | None
        ) = None,
        message_repository: (
            ConversationMessageRepository | None
        ) = None,
        user_repository: UserRepository | None = None,
    ) -> None:
        self.conversation_repository = (
            conversation_repository
            or ConversationRepository()
        )

        self.message_repository = (
            message_repository
            or ConversationMessageRepository()
        )

        self.user_repository = (
            user_repository
            or UserRepository()
        )

    def create_conversation(
        self,
        db: Session,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None = None,
    ) -> Conversation:
        user = self.user_repository.get_by_id(
            db,
            user_id,
        )

        if user is None:
            raise ValueError(
                "User not found."
            )

        if user.tenant_id != tenant_id:
            raise ValueError(
                "User does not belong to the specified tenant."
            )

        normalized_title = (
            title.strip()
            if title is not None
            else None
        )

        if normalized_title == "":
            normalized_title = None

        return self.conversation_repository.create(
            db,
            tenant_id=tenant_id,
            user_id=user_id,
            title=normalized_title,
        )

    def list_user_conversations(
        self,
        db: Session,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[Conversation]:
        return self.conversation_repository.list_by_user(
            db,
            tenant_id=tenant_id,
            user_id=user_id,
        )

    def get_conversation(
        self,
        db: Session,
        *,
        conversation_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Conversation | None:
        conversation = (
            self.conversation_repository.get_by_id(
                db,
                conversation_id,
            )
        )

        if conversation is None:
            return None

        if conversation.tenant_id != tenant_id:
            return None

        if conversation.user_id != user_id:
            return None

        return conversation

    def list_messages(
        self,
        db: Session,
        *,
        conversation_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[ConversationMessage]:
        conversation = self.get_conversation(
            db,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        if conversation is None:
            raise ValueError(
                "Conversation not found."
            )

        return self.message_repository.list_by_conversation(
            db,
            conversation_id,
        )

    def append_user_message(
        self,
        db: Session,
        *,
        conversation_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
    ) -> ConversationMessage:
        return self._append_message(
            db,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            role=MessageRole.USER,
            content=content,
            sources=None,
        )

    def append_assistant_message(
        self,
        db: Session,
        *,
        conversation_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        sources: list | None = None,
    ) -> ConversationMessage:
        return self._append_message(
            db,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=content,
            sources=sources,
        )

    def _append_message(
        self,
        db: Session,
        *,
        conversation_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        role: MessageRole,
        content: str,
        sources: list | None,
    ) -> ConversationMessage:
        conversation = self.get_conversation(
            db,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        if conversation is None:
            raise ValueError(
                "Conversation not found."
            )

        normalized_content = content.strip()

        if not normalized_content:
            raise ValueError(
                "Message content cannot be empty."
            )

        message_index = (
            self.message_repository
            .get_next_message_index(
                db,
                conversation_id,
            )
        )

        return self.message_repository.create(
            db,
            conversation_id=conversation_id,
            message_index=message_index,
            role=role,
            content=normalized_content,
            sources=sources,
        )