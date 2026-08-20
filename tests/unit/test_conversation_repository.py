from unittest.mock import MagicMock
from uuid import uuid4

from app.models.conversation import Conversation
from app.models.enums import MessageRole
from app.repositories.conversation import (
    ConversationRepository,
)
from app.repositories.conversation_message import (
    ConversationMessageRepository,
)


def test_create_conversation():
    db = MagicMock()
    repository = ConversationRepository()

    tenant_id = uuid4()
    user_id = uuid4()

    conversation = repository.create(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        title="Knowledge questions",
    )

    assert conversation.tenant_id == tenant_id
    assert conversation.user_id == user_id
    assert conversation.title == (
        "Knowledge questions"
    )

    db.add.assert_called_once_with(
        conversation,
    )
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(
        conversation,
    )


def test_get_conversation_by_id():
    db = MagicMock()
    repository = ConversationRepository()

    conversation = Conversation(
        tenant_id=uuid4(),
        user_id=uuid4(),
        title="Conversation",
    )

    db.scalar.return_value = conversation

    result = repository.get_by_id(
        db,
        uuid4(),
    )

    assert result is conversation
    db.scalar.assert_called_once()


def test_list_conversations_by_user():
    db = MagicMock()
    repository = ConversationRepository()

    tenant_id = uuid4()
    user_id = uuid4()

    conversations = [
        Conversation(
            tenant_id=tenant_id,
            user_id=user_id,
            title="One",
        ),
        Conversation(
            tenant_id=tenant_id,
            user_id=user_id,
            title="Two",
        ),
    ]

    db.scalars.return_value.all.return_value = (
        conversations
    )

    result = repository.list_by_user(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    assert result == conversations
    db.scalars.assert_called_once()


def test_get_next_message_index_for_empty_conversation():
    db = MagicMock()
    repository = ConversationMessageRepository()

    db.scalar.return_value = -1

    result = repository.get_next_message_index(
        db,
        uuid4(),
    )

    assert result == 0


def test_get_next_message_index():
    db = MagicMock()
    repository = ConversationMessageRepository()

    db.scalar.return_value = 3

    result = repository.get_next_message_index(
        db,
        uuid4(),
    )

    assert result == 4


def test_create_message():
    db = MagicMock()
    repository = ConversationMessageRepository()

    conversation_id = uuid4()

    message = repository.create(
        db,
        conversation_id=conversation_id,
        message_index=0,
        role=MessageRole.USER,
        content="What is KnowledgeHub?",
    )

    assert message.conversation_id == (
        conversation_id
    )
    assert message.message_index == 0
    assert message.role == MessageRole.USER
    assert message.content == (
        "What is KnowledgeHub?"
    )
    assert message.sources is None

    db.add.assert_called_once_with(message)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(message)


def test_create_assistant_message_with_sources():
    db = MagicMock()
    repository = ConversationMessageRepository()

    sources = [
        {
            "document_id": str(uuid4()),
            "chunk_index": 0,
            "similarity": 0.91,
        }
    ]

    message = repository.create(
        db,
        conversation_id=uuid4(),
        message_index=1,
        role=MessageRole.ASSISTANT,
        content="Grounded answer.",
        sources=sources,
    )

    assert message.role == MessageRole.ASSISTANT
    assert message.sources == sources


def test_list_messages_by_conversation():
    db = MagicMock()
    repository = ConversationMessageRepository()

    conversation_id = uuid4()

    messages = [
        MagicMock(),
        MagicMock(),
    ]

    db.scalars.return_value.all.return_value = (
        messages
    )

    result = repository.list_by_conversation(
        db,
        conversation_id,
    )

    assert result == messages
    db.scalars.assert_called_once()