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
    assert hasattr(Document, "tenant")
    assert hasattr(Document, "chunks")
    assert hasattr(DocumentChunk, "document")