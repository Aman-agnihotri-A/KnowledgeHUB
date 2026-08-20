from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.core.config import settings
from app.db.session import engine


def _alembic_config() -> Config:
    config = Config("alembic.ini")
    config.set_main_option(
        "sqlalchemy.url",
        settings.database_url,
    )
    return config


def _reset_database() -> None:
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "DROP SCHEMA public CASCADE"
        )
        connection.exec_driver_sql(
            "CREATE SCHEMA public"
        )


def test_migrations_upgrade_to_head() -> None:
    config = _alembic_config()

    _reset_database()

    command.upgrade(config, "head")

    with engine.connect() as connection:
        inspector = inspect(connection)

        tables = set(inspector.get_table_names())

        assert "alembic_version" in tables
        assert "tenants" in tables
        assert "users" in tables
        assert "documents" in tables
        assert "document_chunks" in tables
        chunk_columns = {
            column["name"]: column
            for column in inspector.get_columns(
                "document_chunks"
            )
        }

        assert "embedding" in chunk_columns
        assert chunk_columns["embedding"]["nullable"] is True
        assert "conversations" in tables
        assert "conversation_messages" in tables

        conversation_columns = {
            column["name"]: column
            for column in inspector.get_columns(
                "conversations"
            )
        }

        message_columns = {
            column["name"]: column
            for column in inspector.get_columns(
                "conversation_messages"
            )
        }

        assert "tenant_id" in conversation_columns
        assert "user_id" in conversation_columns
        assert "title" in conversation_columns

        assert "conversation_id" in message_columns
        assert "message_index" in message_columns
        assert "role" in message_columns
        assert "content" in message_columns
        assert "sources" in message_columns


def test_migrations_can_downgrade_and_upgrade() -> None:
    config = _alembic_config()

    _reset_database()

    command.upgrade(config, "head")

    with engine.connect() as connection:
        inspector = inspect(connection)

        tables = set(inspector.get_table_names())

        assert "alembic_version" in tables
        assert "tenants" in tables
        assert "users" in tables
        assert "documents" in tables
        assert "document_chunks" in tables

    command.downgrade(config, "base")

    

    with engine.connect() as connection:
        inspector = inspect(connection)

        tables = set(inspector.get_table_names())

        assert "alembic_version" in tables
        assert "tenants" not in tables
        assert "users" not in tables
        assert "documents" not in tables
        assert "document_chunks" not in tables

    command.upgrade(config, "head")

    with engine.connect() as connection:
        inspector = inspect(connection)

        tables = set(inspector.get_table_names())

        assert "alembic_version" in tables
        assert "tenants" in tables
        assert "users" in tables
        assert "documents" in tables
        assert "document_chunks" in tables
        assert "conversations" in tables
        assert "conversation_messages" in tables

        tenant_columns = {
            column["name"]: column
            for column in inspector.get_columns(
                "tenants"
            )
        }

        user_columns = {
            column["name"]: column
            for column in inspector.get_columns(
                "users"
            )
        }

        document_columns = {
            column["name"]: column
            for column in inspector.get_columns(
                "documents"
            )
        }

        chunk_columns = {
            column["name"]: column
            for column in inspector.get_columns(
                "document_chunks"
            )
        }

        conversation_columns = {
            column["name"]: column
            for column in inspector.get_columns(
                "conversations"
            )
        }

        message_columns = {
            column["name"]: column
            for column in inspector.get_columns(
                "conversation_messages"
            )
        }

        assert tenant_columns["created_at"][
            "default"
        ] is not None
        assert tenant_columns["updated_at"][
            "default"
        ] is not None

        assert user_columns["created_at"][
            "default"
        ] is not None
        assert user_columns["updated_at"][
            "default"
        ] is not None

        assert document_columns["created_at"][
            "default"
        ] is not None
        assert document_columns["updated_at"][
            "default"
        ] is not None

        assert chunk_columns["created_at"][
            "default"
        ] is not None
        assert chunk_columns["updated_at"][
            "default"
        ] is not None

        assert "embedding" in chunk_columns

        assert conversation_columns["tenant_id"][
            "nullable"
        ] is False
        assert conversation_columns["user_id"][
            "nullable"
        ] is False
        assert conversation_columns["title"][
            "nullable"
        ] is True

        assert message_columns["conversation_id"][
            "nullable"
        ] is False
        assert message_columns["message_index"][
            "nullable"
        ] is False
        assert message_columns["role"][
            "nullable"
        ] is False
        assert message_columns["content"][
            "nullable"
        ] is False
        assert message_columns["sources"][
            "nullable"
        ] is True

    with engine.connect() as connection:
        inspector = inspect(connection)

        tables = set(inspector.get_table_names())

        assert "alembic_version" in tables
        assert "tenants" in tables
        assert "users" in tables
        assert "documents" in tables
        assert "document_chunks" in tables
        tenant_columns = {
            column["name"]: column
            for column in inspector.get_columns("tenants")
        }

        user_columns = {
            column["name"]: column
            for column in inspector.get_columns("users")
        }

        document_columns = {
            column["name"]: column
            for column in inspector.get_columns("documents")
        }

        chunk_columns = {
            column["name"]: column
            for column in inspector.get_columns(
                "document_chunks"
            )
        }

        
        assert tenant_columns["created_at"]["default"] is not None
        assert tenant_columns["updated_at"]["default"] is not None

        assert user_columns["created_at"]["default"] is not None
        assert user_columns["updated_at"]["default"] is not None

        assert document_columns["created_at"]["default"] is not None
        assert document_columns["updated_at"]["default"] is not None

        assert chunk_columns["created_at"]["default"] is not None
        assert chunk_columns["updated_at"]["default"] is not None
        assert "embedding" in chunk_columns