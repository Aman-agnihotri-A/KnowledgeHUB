from sqlalchemy import inspect

from app.db import engine
from app.models import Base


def test_database_engine_can_inspect_connection() -> None:
    with engine.connect() as connection:
        inspector = inspect(connection)

        assert inspector is not None


def test_model_metadata_contains_expected_tables() -> None:
    expected_tables = {
        "tenants",
        "users",
        "documents",
        "document_chunks",
    }

    assert expected_tables.issubset(
        Base.metadata.tables.keys()
    )


def test_database_schema_can_be_created_and_inspected() -> None:
    Base.metadata.create_all(bind=engine)

    try:
        with engine.connect() as connection:
            inspector = inspect(connection)

            assert set(inspector.get_table_names()).issuperset(
                {
                    "tenants",
                    "users",
                    "documents",
                    "document_chunks",
                }
            )

            user_foreign_keys = inspector.get_foreign_keys("users")
            document_foreign_keys = inspector.get_foreign_keys("documents")
            chunk_foreign_keys = inspector.get_foreign_keys(
                "document_chunks"
            )

            assert any(
                fk["referred_table"] == "tenants"
                and fk["constrained_columns"] == ["tenant_id"]
                for fk in user_foreign_keys
            )

            assert any(
                fk["referred_table"] == "tenants"
                and fk["constrained_columns"] == ["tenant_id"]
                for fk in document_foreign_keys
            )

            assert any(
                fk["referred_table"] == "users"
                and fk["constrained_columns"] == ["uploaded_by"]
                for fk in document_foreign_keys
            )

            assert any(
                fk["referred_table"] == "documents"
                and fk["constrained_columns"] == ["document_id"]
                for fk in chunk_foreign_keys
            )

            unique_constraints = inspector.get_unique_constraints(
                "document_chunks"
            )

            assert any(
                constraint["name"]
                == "uq_document_chunks_document_index"
                for constraint in unique_constraints
            )
    finally:
        Base.metadata.drop_all(bind=engine)