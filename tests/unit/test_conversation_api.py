from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.conversations import (
    conversation_service,
)
from app.dependencies.auth import get_current_user
from app.main import app
from app.models.enums import UserRole,MessageRole


client = TestClient(app)


def authenticate_as(
    *,
    role: UserRole,
    tenant_id,
):
    user = MagicMock()

    user.id = uuid4()
    user.role = role
    user.tenant_id = tenant_id
    user.is_active = True

    app.dependency_overrides[
        get_current_user
    ] = lambda: user

    return user


def clear_authentication_override():
    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


def test_create_conversation_requires_authentication():
    tenant_id = uuid4()

    response = client.post(
        f"/conversations/{tenant_id}",
        json={
            "title": "Knowledge questions",
        },
    )

    assert response.status_code == 401


def test_create_conversation_rejects_cross_tenant_access():
    requested_tenant_id = uuid4()
    user_tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=user_tenant_id,
    )

    try:
        response = client.post(
            f"/conversations/{requested_tenant_id}",
            json={
                "title": "Should fail",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_super_admin_cannot_use_user_owned_conversation_api():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    try:
        response = client.post(
            f"/conversations/{tenant_id}",
            json={
                "title": "Should fail",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_create_conversation():
    tenant_id = uuid4()
    user = authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    conversation = MagicMock()

    conversation.id = uuid4()
    conversation.tenant_id = tenant_id
    conversation.user_id = user.id
    conversation.title = "Knowledge questions"
    conversation.created_at = (
        "2026-08-21T10:00:00+00:00"
    )
    conversation.updated_at = (
        "2026-08-21T10:00:00+00:00"
    )

    original_create = (
        conversation_service.create_conversation
    )

    conversation_service.create_conversation = (
        MagicMock(
            return_value=conversation,
        )
    )

    try:
        response = client.post(
            f"/conversations/{tenant_id}",
            json={
                "title": "Knowledge questions",
            },
        )

        assert response.status_code == 201

        body = response.json()

        assert body["id"] == str(
            conversation.id,
        )
        assert body["tenant_id"] == str(
            tenant_id,
        )
        assert body["user_id"] == str(
            user.id,
        )
        assert body["title"] == (
            "Knowledge questions"
        )

    finally:
        conversation_service.create_conversation = (
            original_create
        )
        clear_authentication_override()


def test_list_conversations():
    tenant_id = uuid4()

    user = authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    conversation = MagicMock()

    conversation.id = uuid4()
    conversation.tenant_id = tenant_id
    conversation.user_id = user.id
    conversation.title = "First conversation"
    conversation.created_at = (
        "2026-08-21T10:00:00+00:00"
    )
    conversation.updated_at = (
        "2026-08-21T10:00:00+00:00"
    )

    original_list = (
        conversation_service.list_user_conversations
    )

    conversation_service.list_user_conversations = (
        MagicMock(
            return_value=[conversation],
        )
    )

    try:
        response = client.get(
            f"/conversations/{tenant_id}",
        )

        assert response.status_code == 200

        body = response.json()

        assert len(body) == 1
        assert body[0]["id"] == str(
            conversation.id,
        )
        assert body[0]["title"] == (
            "First conversation"
        )

    finally:
        conversation_service.list_user_conversations = (
            original_list
        )
        clear_authentication_override()


def test_get_conversation_rejects_other_user():
    tenant_id = uuid4()
    user = authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    original_get = (
        conversation_service.get_conversation
    )

    conversation_service.get_conversation = (
        MagicMock(
            return_value=None,
        )
    )

    try:
        response = client.get(
            f"/conversations/{tenant_id}/{uuid4()}",
        )

        assert response.status_code == 404

    finally:
        conversation_service.get_conversation = (
            original_get
        )
        clear_authentication_override()


def test_get_conversation_returns_messages():
    tenant_id = uuid4()

    user = authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    conversation_id = uuid4()
    message_id = uuid4()

    conversation = MagicMock()

    conversation.id = conversation_id
    conversation.tenant_id = tenant_id
    conversation.user_id = user.id
    conversation.title = "Knowledge"
    conversation.created_at = (
        "2026-08-21T10:00:00+00:00"
    )
    conversation.updated_at = (
        "2026-08-21T10:01:00+00:00"
    )

    message = MagicMock()

    message.id = message_id
    message.conversation_id = conversation_id
    message.message_index = 0
    message.role = MessageRole.USER
    message.content = "What is KnowledgeHub?"
    message.sources = None
    message.created_at = (
        "2026-08-21T10:00:01+00:00"
    )
    message.updated_at = (
        "2026-08-21T10:00:01+00:00"
    )

    original_get = (
        conversation_service.get_conversation
    )
    original_messages = (
        conversation_service.list_messages
    )

    conversation_service.get_conversation = (
        MagicMock(
            return_value=conversation,
        )
    )

    conversation_service.list_messages = (
        MagicMock(
            return_value=[message],
        )
    )

    try:
        response = client.get(
            f"/conversations/{tenant_id}/{conversation_id}",
        )

        assert response.status_code == 200

        body = response.json()

        assert body["id"] == str(
            conversation_id,
        )
        assert len(body["messages"]) == 1
        assert body["messages"][0]["id"] == str(
            message_id,
        )
        assert body["messages"][0]["content"] == (
            "What is KnowledgeHub?"
        )

    finally:
        conversation_service.get_conversation = (
            original_get
        )
        conversation_service.list_messages = (
            original_messages
        )
        clear_authentication_override()