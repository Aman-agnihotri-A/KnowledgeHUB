import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.db import engine
from app.models import (
    Base,
    Document,
    DocumentChunk,
    DocumentStatus,
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