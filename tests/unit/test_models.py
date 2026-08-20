from sqlalchemy import inspect

from app.models import Base
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.tenant import Tenant
from app.models.user import User


def test_all_domain_models_are_registered() -> None:
    tables = Base.metadata.tables

    assert "tenants" in tables
    assert "users" in tables
    assert "documents" in tables
    assert "document_chunks" in tables


def test_domain_model_relationships_are_configured() -> None:
    assert hasattr(Tenant, "users")
    assert hasattr(Tenant, "documents")

    assert hasattr(User, "tenant")
    assert hasattr(User, "uploaded_documents")

    assert hasattr(Document, "tenant")
    assert hasattr(Document, "uploaded_by_user")
    assert hasattr(Document, "chunks")

    assert hasattr(DocumentChunk, "document")


def test_foreign_keys_are_correct() -> None:
    users = inspect(User).local_table
    documents = inspect(Document).local_table
    chunks = inspect(DocumentChunk).local_table

    user_fks = {
        fk.target_fullname
        for fk in users.c.tenant_id.foreign_keys
    }

    document_tenant_fks = {
        fk.target_fullname
        for fk in documents.c.tenant_id.foreign_keys
    }

    document_user_fks = {
        fk.target_fullname
        for fk in documents.c.uploaded_by.foreign_keys
    }

    chunk_fks = {
        fk.target_fullname
        for fk in chunks.c.document_id.foreign_keys
    }

    assert user_fks == {"tenants.id"}
    assert document_tenant_fks == {"tenants.id"}
    assert document_user_fks == {"users.id"}
    assert chunk_fks == {"documents.id"}


def test_document_chunk_has_unique_document_index_constraint() -> None:
    table = inspect(DocumentChunk).local_table

    constraints = {
        constraint.name
        for constraint in table.constraints
        if constraint.name is not None
    }

    assert "uq_document_chunks_document_index" in constraints

def test_document_status_values():
    from app.models.enums import DocumentStatus

    assert DocumentStatus.UPLOADED.value == "uploaded"
    assert DocumentStatus.PROCESSING.value == "processing"
    assert DocumentStatus.READY.value == "ready"
    assert DocumentStatus.FAILED.value == "failed"