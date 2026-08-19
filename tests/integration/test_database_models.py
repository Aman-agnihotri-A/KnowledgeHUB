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