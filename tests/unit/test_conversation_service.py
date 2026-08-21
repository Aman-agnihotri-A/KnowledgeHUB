from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.conversation import (
    Conversation,
    ConversationMessage,
)
from app.models.enums import MessageRole, UserRole
from app.services.conversation import (
    ConversationService,
)


def make_user(
    *,
    user_id,
    tenant_id,
):
    user = MagicMock()
    user.id = user_id
    user.tenant_id = tenant_id
    user.role = UserRole.SUB_USER
    user.is_active = True
    return user


def test_create_conversation_validates_user_tenant():
    db = MagicMock()

    repository = MagicMock()
    message_repository = MagicMock()
    user_repository = MagicMock()

    tenant_id = uuid4()
    user_id = uuid4()

    user_repository.get_by_id.return_value = (
        make_user(
            user_id=user_id,
            tenant_id=tenant_id,
        )
    )

    conversation = Conversation(
        tenant_id=tenant_id,
        user_id=user_id,
        title="Test",
    )

    repository.create.return_value = conversation

    service = ConversationService(
        conversation_repository=repository,
        message_repository=message_repository,
        user_repository=user_repository,
    )

    result = service.create_conversation(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        title="  Test  ",
    )

    assert result is conversation

    repository.create.assert_called_once_with(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        title="Test",
    )


def test_create_conversation_rejects_missing_user():
    db = MagicMock()

    user_repository = MagicMock()
    user_repository.get_by_id.return_value = None

    service = ConversationService(
        conversation_repository=MagicMock(),
        message_repository=MagicMock(),
        user_repository=user_repository,
    )

    with pytest.raises(
        ValueError,
        match="User not found",
    ):
        service.create_conversation(
            db,
            tenant_id=uuid4(),
            user_id=uuid4(),
        )


def test_create_conversation_rejects_cross_tenant_user():
    db = MagicMock()

    tenant_id = uuid4()

    user_repository = MagicMock()
    user_repository.get_by_id.return_value = (
        make_user(
            user_id=uuid4(),
            tenant_id=uuid4(),
        )
    )

    service = ConversationService(
        conversation_repository=MagicMock(),
        message_repository=MagicMock(),
        user_repository=user_repository,
    )

    with pytest.raises(
        ValueError,
        match="does not belong",
    ):
        service.create_conversation(
            db,
            tenant_id=tenant_id,
            user_id=uuid4(),
        )


def test_get_conversation_enforces_tenant_and_owner():
    db = MagicMock()

    tenant_id = uuid4()
    user_id = uuid4()
    conversation_id = uuid4()

    repository = MagicMock()

    conversation = Conversation(
        tenant_id=tenant_id,
        user_id=user_id,
        title="Private",
    )

    repository.get_by_id.return_value = (
        conversation
    )

    service = ConversationService(
        conversation_repository=repository,
        message_repository=MagicMock(),
        user_repository=MagicMock(),
    )

    assert (
        service.get_conversation(
            db,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        is conversation
    )

    assert (
        service.get_conversation(
            db,
            conversation_id=conversation_id,
            tenant_id=uuid4(),
            user_id=user_id,
        )
        is None
    )

    assert (
        service.get_conversation(
            db,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=uuid4(),
        )
        is None
    )


def test_append_user_message():
    db = MagicMock()

    tenant_id = uuid4()
    user_id = uuid4()
    conversation_id = uuid4()

    conversation_repository = MagicMock()
    message_repository = MagicMock()

    conversation_repository.get_by_id.return_value = (
        Conversation(
            id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title="Chat",
        )
    )

    message_repository.get_next_message_index.return_value = (
        2
    )

    message = ConversationMessage(
        conversation_id=conversation_id,
        message_index=2,
        role=MessageRole.USER,
        content="Question",
    )

    message_repository.create.return_value = message

    service = ConversationService(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        user_repository=MagicMock(),
    )

    result = service.append_user_message(
        db,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=user_id,
        content="  Question  ",
    )

    assert result is message

    message_repository.create.assert_called_once_with(
        db,
        conversation_id=conversation_id,
        message_index=2,
        role=MessageRole.USER,
        content="Question",
        sources=None,
    )


def test_append_assistant_message_with_sources():
    db = MagicMock()

    tenant_id = uuid4()
    user_id = uuid4()
    conversation_id = uuid4()

    conversation_repository = MagicMock()
    message_repository = MagicMock()

    conversation_repository.get_by_id.return_value = (
        Conversation(
            id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )
    )

    message_repository.get_next_message_index.return_value = (
        1
    )

    sources = [
        {
            "document_id": str(uuid4()),
            "chunk_index": 2,
            "similarity": 0.94,
        }
    ]

    message = ConversationMessage(
        conversation_id=conversation_id,
        message_index=1,
        role=MessageRole.ASSISTANT,
        content="Answer",
        sources=sources,
    )

    message_repository.create.return_value = message

    service = ConversationService(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        user_repository=MagicMock(),
    )

    result = service.append_assistant_message(
        db,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=user_id,
        content="Answer",
        sources=sources,
    )

    assert result is message

    message_repository.create.assert_called_once_with(
        db,
        conversation_id=conversation_id,
        message_index=1,
        role=MessageRole.ASSISTANT,
        content="Answer",
        sources=sources,
    )


def test_append_message_rejects_empty_content():
    db = MagicMock()

    tenant_id = uuid4()
    user_id = uuid4()
    conversation_id = uuid4()

    conversation_repository = MagicMock()

    conversation_repository.get_by_id.return_value = (
        Conversation(
            id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )
    )

    service = ConversationService(
        conversation_repository=conversation_repository,
        message_repository=MagicMock(),
        user_repository=MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="Message content cannot be empty",
    ):
        service.append_user_message(
            db,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            content="   ",
        )


def test_append_message_rejects_inaccessible_conversation():
    db = MagicMock()

    conversation_repository = MagicMock()
    conversation_repository.get_by_id.return_value = (
        None
    )

    service = ConversationService(
        conversation_repository=conversation_repository,
        message_repository=MagicMock(),
        user_repository=MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="Conversation not found",
    ):
        service.append_user_message(
            db,
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            content="Question",
        )

def test_list_recent_messages_enforces_conversation_access():
    db = MagicMock()

    tenant_id = uuid4()
    user_id = uuid4()
    conversation_id = uuid4()

    conversation_repository = MagicMock()
    message_repository = MagicMock()

    conversation_repository.get_by_id.return_value = (
        Conversation(
            id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title="History",
        )
    )

    messages = [
        ConversationMessage(
            conversation_id=conversation_id,
            message_index=0,
            role=MessageRole.USER,
            content="First",
        ),
        ConversationMessage(
            conversation_id=conversation_id,
            message_index=1,
            role=MessageRole.ASSISTANT,
            content="Second",
        ),
    ]

    message_repository.list_recent_by_conversation.return_value = (
        messages
    )

    service = ConversationService(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        user_repository=MagicMock(),
    )

    result = service.list_recent_messages(
        db,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=user_id,
        limit=10,
    )

    assert result == messages

    message_repository.list_recent_by_conversation.assert_called_once_with(
        db,
        conversation_id,
        limit=10,
    )

def test_list_recent_messages_rejects_inaccessible_conversation():
    db = MagicMock()

    conversation_repository = MagicMock()

    conversation_repository.get_by_id.return_value = (
        Conversation(
            id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            title="Private",
        )
    )

    service = ConversationService(
        conversation_repository=conversation_repository,
        message_repository=MagicMock(),
        user_repository=MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="Conversation not found",
    ):
        service.list_recent_messages(
            db,
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            limit=10,
        )