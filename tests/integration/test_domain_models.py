import uuid 

import pytest
from sqlalchemy.exc import IntegrityError

from app.db import engine
from app.models import (
    Base,
    Conversation,
    ConversationMessage,
    Document,
    DocumentChunk,
    DocumentStatus,
    MessageRole,
    Tenant,
    User,
    UserRole,
)


@pytest.fixture(autouse=True)
def database_schema():
    Base.metadata.create_all(bind=engine)

    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine)


def test_domain_models_can_be_persisted() -> None:
    from sqlalchemy.orm import Session

    tenant = Tenant(
        name="Acme Corporation",
        slug="acme",
    )

    with Session(engine) as session:
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email="admin@acme.example",
            hashed_password="hashed-password",
            full_name="Acme Admin",
            role=UserRole.TENANT_ADMIN,
        )

        session.add(user)
        session.flush()

        document = Document(
            tenant_id=tenant.id,
            uploaded_by=user.id,
            filename="handbook.pdf",
            storage_path="documents/acme/handbook.pdf",
        )

        session.add(document)
        session.flush()

        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            content="KnowledgeHub test content.",
        )

        session.add(chunk)
        session.commit()

        assert tenant.id is not None
        assert user.id is not None
        assert document.id is not None
        assert chunk.id is not None


def test_document_chunk_index_must_be_unique_per_document() -> None:
    from sqlalchemy.orm import Session

    tenant = Tenant(
        name="Acme Corporation",
        slug="acme",
    )

    with Session(engine) as session:
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email="admin@acme.example",
            hashed_password="hashed-password",
            full_name="Acme Admin",
            role=UserRole.TENANT_ADMIN,
        )

        session.add(user)
        session.flush()

        document = Document(
            tenant_id=tenant.id,
            uploaded_by=user.id,
            filename="handbook.pdf",
            storage_path="documents/acme/handbook.pdf",
            status=DocumentStatus.UPLOADED,
        )

        session.add(document)
        session.flush()

        session.add_all(
            [
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=0,
                    content="First chunk",
                ),
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=0,
                    content="Duplicate chunk index",
                ),
            ]
        )

        with pytest.raises(IntegrityError):
            session.commit()


def test_same_chunk_index_is_allowed_for_different_documents() -> None:
    from sqlalchemy.orm import Session

    tenant = Tenant(
        name="Acme Corporation",
        slug="acme",
    )

    with Session(engine) as session:
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email="admin@acme.example",
            hashed_password="hashed-password",
            full_name="Acme Admin",
            role=UserRole.TENANT_ADMIN,
        )

        session.add(user)
        session.flush()

        documents = [
            Document(
                tenant_id=tenant.id,
                uploaded_by=user.id,
                filename=f"document-{index}.pdf",
                storage_path=f"documents/acme/document-{index}.pdf",
            )
            for index in range(2)
        ]

        session.add_all(documents)
        session.flush()

        session.add_all(
            [
                DocumentChunk(
                    document_id=documents[0].id,
                    chunk_index=0,
                    content="Document one chunk",
                ),
                DocumentChunk(
                    document_id=documents[1].id,
                    chunk_index=0,
                    content="Document two chunk",
                ),
            ]
        )

        session.commit()

        assert documents[0].id != documents[1].id


def test_tenant_can_be_deleted_with_children() -> None:
    from sqlalchemy.orm import Session

    tenant = Tenant(
        name="Delete Me",
        slug="delete-me",
    )

    with Session(engine) as session:
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email="admin@delete-me.example",
            hashed_password="hashed-password",
            full_name="Delete Me Admin",
            role=UserRole.TENANT_ADMIN,
        )

        session.add(user)
        session.flush()

        document = Document(
            tenant_id=tenant.id,
            uploaded_by=user.id,
            filename="delete.pdf",
            storage_path="documents/delete.pdf",
        )

        session.add(document)
        session.flush()

        session.add(
            DocumentChunk(
                document_id=document.id,
                chunk_index=0,
                content="Delete me",
            )
        )

        session.commit()

        tenant_id = tenant.id

        session.delete(tenant)
        session.commit()

        assert (
            session.get(Tenant, tenant_id)
            is None
        )


def test_uuid_primary_keys_are_generated() -> None:
    from sqlalchemy.orm import Session

    tenant = Tenant(
        name="UUID Test",
        slug=f"uuid-{uuid.uuid4()}",
    )

    with Session(engine) as session:
        session.add(tenant)
        session.commit()

        assert isinstance(tenant.id, uuid.UUID)

def test_document_status_is_persisted() -> None:
    from sqlalchemy.orm import Session

    tenant = Tenant(
        name="Status Tenant",
        slug="status-tenant",
    )

    with Session(engine) as session:
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email="status-admin@example.com",
            hashed_password="hashed-password",
            full_name="Status Admin",
            role=UserRole.TENANT_ADMIN,
        )

        session.add(user)
        session.flush()

        document = Document(
            tenant_id=tenant.id,
            uploaded_by=user.id,
            filename="status-test.pdf",
            storage_path="documents/status-test.pdf",
            status=DocumentStatus.PROCESSING,
        )

        session.add(document)
        session.commit()

        document_id = document.id

        session.expire_all()

        persisted_document = session.get(
            Document,
            document_id,
        )

        assert persisted_document is not None
        assert persisted_document.status == DocumentStatus.PROCESSING

def test_user_active_status_is_persisted() -> None:
    from sqlalchemy.orm import Session

    tenant = Tenant(
        name="Lifecycle Tenant",
        slug="lifecycle-tenant",
    )

    with Session(engine) as session:
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email="lifecycle@example.com",
            hashed_password="hashed-password",
            full_name="Lifecycle User",
            role=UserRole.SUB_USER,
            is_active=True,
        )

        session.add(user)
        session.commit()

        user_id = user.id

        user.is_active = False
        session.commit()

        session.expire_all()

        persisted_user = session.get(
            User,
            user_id,
        )

        assert persisted_user is not None
        assert persisted_user.is_active is False

def test_documents_can_be_filtered_by_status() -> None:
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    tenant = Tenant(
        name="Filter Tenant",
        slug="filter-tenant",
    )

    with Session(engine) as session:
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email="filter@example.com",
            hashed_password="hashed-password",
            full_name="Filter User",
            role=UserRole.SUB_USER,
            is_active=True,
        )

        session.add(user)
        session.flush()

        processing_document = Document(
            tenant_id=tenant.id,
            uploaded_by=user.id,
            filename="processing.pdf",
            storage_path="documents/processing.pdf",
            status=DocumentStatus.PROCESSING,
        )

        ready_document = Document(
            tenant_id=tenant.id,
            uploaded_by=user.id,
            filename="ready.pdf",
            storage_path="documents/ready.pdf",
            status=DocumentStatus.READY,
        )

        session.add_all(
            [
                processing_document,
                ready_document,
            ]
        )
        session.commit()

        statement = select(Document).where(
            Document.tenant_id == tenant.id,
            Document.status == DocumentStatus.PROCESSING,
        )

        result = list(
            session.scalars(statement).all()
        )

        assert len(result) == 1
        assert result[0].filename == "processing.pdf"
        assert result[0].status == DocumentStatus.PROCESSING

def test_document_chunk_embedding_can_be_persisted() -> None:
    from sqlalchemy.orm import Session

    tenant = Tenant(
        name="Embedding Corporation",
        slug="embedding-corp",
    )

    with Session(engine) as session:
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email="admin@embedding.example",
            hashed_password="hashed-password",
            full_name="Embedding Admin",
            role=UserRole.TENANT_ADMIN,
        )

        session.add(user)
        session.flush()

        document = Document(
            tenant_id=tenant.id,
            uploaded_by=user.id,
            filename="embedding.pdf",
            storage_path="documents/embedding.pdf",
            status=DocumentStatus.READY,
        )

        session.add(document)
        session.flush()

        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            content="Persisted embedding",
            embedding=[
                0.1,
                0.2,
                0.3,
                0.4,
            ],
        )

        session.add(chunk)
        session.commit()

        session.refresh(chunk)

        assert chunk.embedding == [
            0.1,
            0.2,
            0.3,
            0.4,
        ]

def test_conversation_and_messages_can_be_persisted() -> None:
    from sqlalchemy.orm import Session

    tenant = Tenant(
        name="Conversation Tenant",
        slug="conversation-tenant",
    )

    with Session(engine) as session:
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email="conversation@example.com",
            hashed_password="hashed-password",
            full_name="Conversation User",
            role=UserRole.SUB_USER,
        )

        session.add(user)
        session.flush()

        conversation = Conversation(
            tenant_id=tenant.id,
            user_id=user.id,
            title="Knowledge discussion",
        )

        session.add(conversation)
        session.flush()

        user_message = ConversationMessage(
            conversation_id=conversation.id,
            message_index=0,
            role=MessageRole.USER,
            content="What is KnowledgeHub?",
        )

        assistant_message = ConversationMessage(
            conversation_id=conversation.id,
            message_index=1,
            role=MessageRole.ASSISTANT,
            content="KnowledgeHub is a knowledge platform.",
            sources=[
                {
                    "document_id": str(uuid.uuid4()),
                    "chunk_index": 0,
                    "similarity": 0.94,
                }
            ],
        )

        session.add_all(
            [
                user_message,
                assistant_message,
            ]
        )

        session.commit()

        assert conversation.id is not None
        assert user_message.id is not None
        assert assistant_message.id is not None

        session.expire_all()

        persisted = session.get(
            Conversation,
            conversation.id,
        )

        assert persisted is not None
        assert len(persisted.messages) == 2
        assert (
            persisted.messages[0].role
            == MessageRole.USER
        )
        assert (
            persisted.messages[1].role
            == MessageRole.ASSISTANT
        )


def test_conversation_message_index_must_be_unique() -> None:
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import IntegrityError

    tenant = Tenant(
        name="Message Index Tenant",
        slug="message-index-tenant",
    )

    with Session(engine) as session:
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email="message-index@example.com",
            hashed_password="hashed-password",
            full_name="Message Index User",
            role=UserRole.SUB_USER,
        )

        session.add(user)
        session.flush()

        conversation = Conversation(
            tenant_id=tenant.id,
            user_id=user.id,
            title="Indexed",
        )

        session.add(conversation)
        session.flush()

        session.add_all(
            [
                ConversationMessage(
                    conversation_id=conversation.id,
                    message_index=0,
                    role=MessageRole.USER,
                    content="First",
                ),
                ConversationMessage(
                    conversation_id=conversation.id,
                    message_index=0,
                    role=MessageRole.ASSISTANT,
                    content="Duplicate",
                ),
            ]
        )

        with pytest.raises(IntegrityError):
            session.commit()


def test_tenant_deletion_cascades_conversations() -> None:
    from sqlalchemy.orm import Session

    tenant = Tenant(
        name="Conversation Delete Tenant",
        slug="conversation-delete-tenant",
    )

    with Session(engine) as session:
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email="conversation-delete@example.com",
            hashed_password="hashed-password",
            full_name="Delete User",
            role=UserRole.SUB_USER,
        )

        session.add(user)
        session.flush()

        conversation = Conversation(
            tenant_id=tenant.id,
            user_id=user.id,
            title="Delete me",
        )

        session.add(conversation)
        session.flush()

        session.add(
            ConversationMessage(
                conversation_id=conversation.id,
                message_index=0,
                role=MessageRole.USER,
                content="Delete me too",
            )
        )

        session.commit()

        conversation_id = conversation.id

        session.delete(tenant)
        session.commit()

        assert (
            session.get(
                Conversation,
                conversation_id,
            )
            is None
        )

def test_conversation_message_supports_rag_source_metadata():
    from sqlalchemy.orm import Session

    tenant = Tenant(
        name="RAG Tenant",
        slug="rag-tenant",
    )

    with Session(engine) as session:
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email="rag-user@example.com",
            hashed_password="hashed-password",
            full_name="RAG User",
            role=UserRole.SUB_USER,
        )

        session.add(user)
        session.flush()

        conversation = Conversation(
            tenant_id=tenant.id,
            user_id=user.id,
            title="RAG conversation",
        )

        session.add(conversation)
        session.flush()

        sources = [
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "document_filename": "handbook.pdf",
                "chunk_index": 2,
                "similarity": 0.94,
            }
        ]

        message = ConversationMessage(
            conversation_id=conversation.id,
            message_index=0,
            role=MessageRole.ASSISTANT,
            content="Grounded answer.",
            sources=sources,
        )

        session.add(message)
        session.commit()
        session.refresh(message)

        assert message.sources == sources