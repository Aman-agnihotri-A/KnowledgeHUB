from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.rag import rag_service
from app.dependencies.auth import get_current_user
from app.main import app
from app.models.enums import UserRole
from app.rag.qa import RAGAnswer, RAGSource


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


def test_rag_requires_authentication():
    tenant_id = uuid4()

    response = client.post(
        f"/rag/{tenant_id}/ask",
        json={
            "question": "What is KnowledgeHub?",
        },
    )

    assert response.status_code == 401


def test_rag_rejects_cross_tenant_access():
    requested_tenant_id = uuid4()
    user_tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=user_tenant_id,
    )

    try:
        response = client.post(
            f"/rag/{requested_tenant_id}/ask",
            json={
                "question": "What is KnowledgeHub?",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_super_admin_cannot_use_user_rag_endpoint():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
    )

    try:
        response = client.post(
            f"/rag/{tenant_id}/ask",
            json={
                "question": "What is KnowledgeHub?",
            },
        )

        assert response.status_code == 403

    finally:
        clear_authentication_override()


def test_rag_returns_grounded_answer():
    tenant_id = uuid4()

    user = authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    source = RAGSource(
        chunk_id=uuid4(),
        document_id=uuid4(),
        document_filename="handbook.pdf",
        chunk_index=2,
        similarity=0.94,
    )

    result = RAGAnswer(
        question="What framework does KnowledgeHub use?",
        answer="KnowledgeHub uses FastAPI.",
        abstained=False,
        sources=[source],
        conversation_id=None,
    )

    original_ask = rag_service.ask
    mock_ask = MagicMock(return_value=result)
    rag_service.ask = mock_ask

    try:
        response = client.post(
            f"/rag/{tenant_id}/ask",
            json={
                "question": (
                    "What framework does KnowledgeHub use?"
                ),
                "top_k": 5,
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert body["question"] == (
            "What framework does KnowledgeHub use?"
        )
        assert body["answer"] == (
            "KnowledgeHub uses FastAPI."
        )
        assert body["abstained"] is False
        assert body["conversation_id"] is None

        assert len(body["sources"]) == 1

        assert body["sources"][0][
            "document_filename"
        ] == "handbook.pdf"

        assert body["sources"][0][
            "chunk_index"
        ] == 2

        mock_ask.assert_called_once()

        call = mock_ask.call_args

        assert call.kwargs["tenant_id"] == tenant_id
        assert call.kwargs["user_id"] == user.id
        assert call.kwargs["question"] == (
            "What framework does KnowledgeHub use?"
        )
        assert call.kwargs["top_k"] == 5
        assert call.kwargs["conversation_id"] is None

    finally:
        rag_service.ask = original_ask
        clear_authentication_override()


def test_rag_passes_conversation_id():
    tenant_id = uuid4()
    conversation_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    result = RAGAnswer(
        question="What framework does it use?",
        answer="It uses FastAPI.",
        abstained=False,
        sources=[],
        conversation_id=conversation_id,
    )

    original_ask = rag_service.ask
    mock_ask = MagicMock(return_value=result)
    rag_service.ask = mock_ask

    try:
        response = client.post(
            f"/rag/{tenant_id}/ask",
            json={
                "question": "What framework does it use?",
                "conversation_id": str(
                    conversation_id,
                ),
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert body["conversation_id"] == str(
            conversation_id,
        )

        assert mock_ask.call_args.kwargs[
            "conversation_id"
        ] == conversation_id

    finally:
        rag_service.ask = original_ask
        clear_authentication_override()


def test_rag_returns_abstention():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    result = RAGAnswer(
        question="Unknown question",
        answer=None,
        abstained=True,
        sources=[],
        conversation_id=None,
    )

    original_ask = rag_service.ask
    rag_service.ask = MagicMock(
        return_value=result,
    )

    try:
        response = client.post(
            f"/rag/{tenant_id}/ask",
            json={
                "question": "Unknown question",
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert body["answer"] is None
        assert body["abstained"] is True
        assert body["sources"] == []

    finally:
        rag_service.ask = original_ask
        clear_authentication_override()


def test_rag_maps_service_error_to_400():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    original_ask = rag_service.ask
    rag_service.ask = MagicMock(
        side_effect=ValueError(
            "Conversation not found.",
        ),
    )

    try:
        response = client.post(
            f"/rag/{tenant_id}/ask",
            json={
                "question": "What is KnowledgeHub?",
                "conversation_id": str(uuid4()),
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Conversation not found."
        )

    finally:
        rag_service.ask = original_ask
        clear_authentication_override()


def test_rag_rejects_invalid_top_k():
    tenant_id = uuid4()

    authenticate_as(
        role=UserRole.SUB_USER,
        tenant_id=tenant_id,
    )

    try:
        response = client.post(
            f"/rag/{tenant_id}/ask",
            json={
                "question": "What is KnowledgeHub?",
                "top_k": 0,
            },
        )

        assert response.status_code == 422

    finally:
        clear_authentication_override()